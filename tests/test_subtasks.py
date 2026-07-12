"""Subtask stack — planner pushes an ordered list, coder pulls one at a time and
completes them in order. Backed by a JSON file beside the run log."""

from codesquad.interceptor import RunLog
from codesquad.tools import subtasks


def test_push_pull_complete_in_order(tmp_path):
    RunLog.start(tmp_path)
    assert "3" in subtasks.set_subtasks.invoke({"subtasks": ["a", "b", "c"]})

    assert "subtask 1/3: a" in subtasks.next_subtask.invoke({})
    assert "next_subtask peeks, does not advance"  # re-reading gives the same one
    assert "subtask 1/3: a" in subtasks.next_subtask.invoke({})

    subtasks.complete_subtask.invoke({})
    assert "subtask 2/3: b" in subtasks.next_subtask.invoke({})

    subtasks.complete_subtask.invoke({})
    subtasks.complete_subtask.invoke({})
    assert "all subtasks done" in subtasks.next_subtask.invoke({})
    assert "no subtask to complete" in subtasks.complete_subtask.invoke({})


def test_set_subtasks_overwrites(tmp_path):
    RunLog.start(tmp_path)
    subtasks.set_subtasks.invoke({"subtasks": ["old"]})
    subtasks.complete_subtask.invoke({})
    subtasks.set_subtasks.invoke({"subtasks": ["fresh"]})
    assert "subtask 1/1: fresh" in subtasks.next_subtask.invoke({})


def test_bump_review_counts_per_subtask(tmp_path):
    RunLog.start(tmp_path)
    subtasks.set_subtasks.invoke({"subtasks": ["a", "b"]})
    assert subtasks.bump_review() == 1
    assert subtasks.bump_review() == 2
    subtasks.complete_subtask.invoke({})  # next subtask starts with a fresh counter
    assert subtasks.bump_review() == 1


def test_bump_review_without_stack_is_zero(tmp_path):
    RunLog.start(tmp_path)  # no subtasks pushed — cap does not apply
    assert subtasks.bump_review() == 0
    subtasks.set_subtasks.invoke({"subtasks": ["only"]})
    subtasks.complete_subtask.invoke({})  # exhausted stack behaves the same
    assert subtasks.bump_review() == 0
