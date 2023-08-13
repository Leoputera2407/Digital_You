from pydantic import BaseModel


class Person(BaseModel):
    name: str


class Label(BaseModel):
    name: str


class PullRequest(BaseModel):
    title: str
    body: str
    html_url: str
    number: int
    created_at: float | None
    updated_at: float | None
    closed_at: float | None
    merged_at: float | None
    merged: bool | None
    state: str
    author: Person | None
    reviewers: list[Person]
    assignees: list[Person]
    labels: list[Label]
    comments: int | None
    commits: int | None

    @property
    def author_name(self) -> str:
        return self.author.name if self.author else ""

    @property
    def reviewer_names(self) -> str:
        return ",".join([reviewer.name for reviewer in self.reviewers])

    @property
    def assignee_names(self) -> str:
        return ",".join([assignee.name for assignee in self.assignees])

    @property
    def label_names(self) -> str:
        return ",".join([label.name for label in self.labels])
