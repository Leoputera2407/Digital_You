from typing import List, Optional

from pydantic import BaseModel


class Person(BaseModel):
    id: str
    name: str
    email: str


class Label(BaseModel):
    name: str


class Issue(BaseModel):
    id: str
    title: str
    description: str
    url: str
    created_at: Optional[float]
    updated_at: Optional[float]
    archived_at: Optional[float]
    assignee: Optional[Person]
    labels: List[Label]

    @property
    def assignee_names(self) -> str:
        return self.assignee.name if self.assignee else ""

    @property
    def label_names(self) -> str:
        return ",".join([label.name for label in self.labels])


class LinearTeam(BaseModel):
    id: str
    name: str


class LinearOrganization(BaseModel):
    id: str
    name: str
    teams: list[LinearTeam]
