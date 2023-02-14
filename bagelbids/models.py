import uuid
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl

UUID_PATTERN = r"[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$"
BAGEL_UUID_PATTERN = r"^bagel:" + UUID_PATTERN


class Bagel(BaseModel):
    """identifier has to be a valid UUID prepended by the bagel: namespace
    by default, a random (uuid4) string UUID will be created"""

    identifier: str = Field(
        regex=BAGEL_UUID_PATTERN,
        default_factory=lambda: "bagel:" + str(uuid.uuid4()),
    )


class Image(BaseModel):
    identifier: str
    schemaKey: Literal["Image"] = Field("Image", readOnly=True)


class Acquisition(Bagel):
    hasContrastType: Image
    schemaKey: Literal["Acquisition"] = Field("Acquisition", readOnly=True)


class Diagnosis(BaseModel):
    identifier: Union[str, HttpUrl]
    schemaKey: Literal["Diagnosis"] = Field("Diagnosis", readOnly=True)


class Assessment(BaseModel):
    identifier: Union[str, HttpUrl]
    schemaKey: Literal["Assessment"] = Field("Assessment", readOnly=True)


class Session(Bagel):
    label: str
    hasAcquisition: List[Acquisition]
    schemaKey: Literal["Session"] = Field("Session", readOnly=True)


class Subject(Bagel):
    label: str
    hasSession: Optional[List[Session]] = None
    age: Optional[float] = None
    sex: Optional[str] = None
    isSubjectGroup: Optional[str] = None
    diagnosis: Optional[List[Diagnosis]] = None
    assessment: Optional[List[Assessment]] = None
    schemaKey: Literal["Subject"] = Field("Subject", readOnly=True)


class Dataset(Bagel):
    label: str
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = Field("Dataset", readOnly=True)
