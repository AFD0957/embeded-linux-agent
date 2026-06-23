"""Pipeline state machine."""

from __future__ import annotations

from enum import Enum


class PipelineState(str, Enum):
    INIT = "init"
    INGEST = "ingest"
    WAIT_VERIFY = "wait_verify"
    BOARD = "board"
    PLAN = "plan"
    GENERATE = "generate"
    BUILD = "build"
    DEPLOY = "deploy"
    TEST = "test"
    REPORT = "report"
    DONE = "done"


PIPELINE_STEPS: list[PipelineState] = [
    PipelineState.INGEST,
    PipelineState.WAIT_VERIFY,
    PipelineState.BOARD,
    PipelineState.PLAN,
    PipelineState.GENERATE,
    PipelineState.BUILD,
    PipelineState.DEPLOY,
    PipelineState.TEST,
    PipelineState.REPORT,
    PipelineState.DONE,
]

TASK_TYPE_TO_STATE: dict[str, PipelineState] = {
    "ingest": PipelineState.INGEST,
    "board_validate": PipelineState.BOARD,
    "plan": PipelineState.PLAN,
    "generate_driver": PipelineState.GENERATE,
    "generate_dts": PipelineState.GENERATE,
    "generate_kbuild": PipelineState.GENERATE,
    "generate_all": PipelineState.GENERATE,
    "build": PipelineState.BUILD,
    "deploy": PipelineState.DEPLOY,
    "test": PipelineState.TEST,
    "report": PipelineState.REPORT,
    "index_kernel": PipelineState.INIT,
    "import_vendor": PipelineState.INIT,
}
