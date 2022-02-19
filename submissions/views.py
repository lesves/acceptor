from django.shortcuts import render, get_object_or_404, redirect

from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import UpdateView, CreateView

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin

from django.core.exceptions import PermissionDenied
from django.http import Http404

from .models import Thesis
from . import models
from . import forms


class IndexView(TemplateView):
	template_name = "submissions/index.html"

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data()
		ctx["subjects"] = models.Subject.objects.all()
		return ctx


class ThesisDetail(UserPassesTestMixin, DetailView):
	model = Thesis

	def test_func(self):
		self.object = self.get_object()
		if self.object.state is not None and self.object.state.code == "defended":
			return True
		return (
			self.request.user.has_perm("submissions.view_thesis") or 
			self.request.user == self.object.author or
			self.request.user == self.object.supervisor or
			self.request.user == self.object.opponent
		)


class OpinionDetail(ThesisDetail):
	"""A detail view for a supervisor/opponent opinion"""

	role = None
	template_name_suffix = "_opinion"

	def get_context_data(self, **kwargs):
		assert self.role is not None

		ctx = super().get_context_data()
		ctx["role"] = self.role
		return ctx

	def get(self, request, *args, **kwargs):
		self.object = self.get_object()
		if self.role == "supervisor" and not self.object.supervisor_opinion:
			raise Http404
		elif self.role == "opponent" and not self.object.opponent_opinion:
			raise Http404

		return super().get(request, *args, **kwargs)


class ThesisUpdate(UserPassesTestMixin, UpdateView):
	model = Thesis

	def test_func(self):
		self.object = self.get_object()
		return (
			self.request.user.has_perm("submissions.change_thesis") or 
			self.request.user == self.object.supervisor or
			self.request.user == self.object.author
		)


class ThesisOpinionUpdate(UserPassesTestMixin, UpdateView):
	model = Thesis
	role = None

	def form_valid(self, form):
		res = super().form_valid(form)
		if (form.instance.state and 
				form.instance.state.code == "submitted" and 
				form.instance.opponent_opinion and 
				form.instance.supervisor_opinion):
			form.instance.set_state_code("defense_ready", self.request.user)

		return res

	def test_func(self):
		"""Check if the user is either the author or the supervisor"""
		self.object = self.get_object()
		if self.role == "supervisor":
			return self.request.user == self.object.supervisor
		elif self.role == "opponent":
			return self.request.user == self.object.opponent
		else:
			raise AssertionError("role should not be None at this time")


class ThesisAssignmentUpdate(ThesisUpdate):
	fields = ["assignment"]

	def post(self, request, *args, **kwargs):
		if request.user == self.object.supervisor and not self.object.is_approved:
			self.object.set_state_code("supervisor_approved", request.user)
		elif request.user == self.object.author and not self.object.is_approved:
			self.object.set_state_code("author_approved", request.user)
		elif request.user.has_perm("submissions.change_thesis"):
			pass
		else:
			raise PermissionDenied("This user cannot update the assignment.")

		return super().post(self, request, *args, **kwargs)


class ThesisRelatedObjectCreate(CreateView):
	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)

		self.thesis = get_object_or_404(Thesis, pk=self.kwargs["pk"])

	def form_valid(self, form):
		form.instance.thesis = self.thesis
		return super().form_valid(form)

	def get_success_url(self):
		return self.thesis.get_absolute_url()


class AttachmentCreate(UserPassesTestMixin, ThesisRelatedObjectCreate):
	template_name = "submissions/submit.html"

	def test_func(self):
		return self.thesis.state.code == "approved" and self.request.user == self.thesis.author


class LogEntryCreate(UserPassesTestMixin, ThesisRelatedObjectCreate):
	model = models.LogEntry
	template_name = "submissions/thesis_form.html"
	fields = ["state"]

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

	def test_func(self):
		return (
			self.request.user == self.thesis.supervisor or 
			self.request.user.has_perm("submissions.change_thesis"))


@login_required
@require_POST
def attachment_delete(request, thesis_pk, pk):
	at = get_object_or_404(models.SubmissionAttachment, pk=pk)
	if str(at.thesis.pk) != thesis_pk:
		raise Http404
	if at.thesis.author != request.user or at.thesis.state.code != "approved":
		raise PermissionDenied()
	at.delete()

	return redirect("thesis-detail", pk=thesis_pk)


@login_required
@require_POST
def approve(request, pk):
	"""The current user approves the thesis assignment"""
	thesis = get_object_or_404(Thesis, pk=pk)
	thesis.approve(request.user)

	return redirect("thesis-detail", pk=pk)


@login_required
@require_POST
def assign(request, pk, role):
	"""Assign the current user of `role` to the thesis with `pk`"""
	thesis = get_object_or_404(Thesis, pk=pk)

	if role == "author" and request.user.has_perm("submissions.author"):
		thesis.author = request.user
	elif role == "supervisor" and request.user.has_perm("submissions.supervisor"):
		thesis.supervisor = request.user
	elif role == "opponent" and request.user.has_perm("submissions.opponent"):
		thesis.opponent = request.user
	else:
		raise PermissionDenied(f"Cannot assign the current user as {role}.")

	thesis.save()

	return redirect("thesis-detail", pk=pk)


@login_required
@require_POST
def unassign(request, pk, role):
	"""
	Cancel the assignment of the current user of the `role`
	to the thesis with the given `pk`
	"""
	thesis = get_object_or_404(Thesis, pk=pk)
	if role == "author" and thesis.author == request.user:
		thesis.author = None
	elif role == "supervisor" and thesis.supervisor == request.user:
		thesis.supervisor = None
	elif role == "opponent" and thesis.opponent == request.user:
		thesis.opponent = None
	else:
		raise PermissionDenied("Cannot unassign. The given user is not assigned.")

	if not thesis.author and not thesis.supervisor and not thesis.opponent:
		thesis.delete()
		return redirect("thesis-list")
	else:
		thesis.save()

	return redirect("thesis-detail", pk=pk)


@login_required
@require_POST
def submit(request, pk):
	"""The thesis is submitted"""
	thesis = get_object_or_404(Thesis, pk=pk)
	if request.user != thesis.author:
		raise PermissionDenied("This user cannot submit this thesis.")
	thesis.submit()
	thesis.save()

	return redirect("thesis-detail", pk=pk)


@login_required
@require_POST
def submit_cancel(request, pk):
	"""Cancel the submission thesis"""
	thesis = get_object_or_404(Thesis, pk=pk)
	if request.user != thesis.author:
		raise PermissionDenied("This user cannot cancel the submission of this thesis.")
	thesis.cancel_submit()
	thesis.save()

	return redirect("thesis-detail", pk=pk)
