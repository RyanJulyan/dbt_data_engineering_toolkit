"""Strongly typed intermediate representation used by every emitter."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .operational import JsonValue
from .version import DEFAULT_DATA_PRODUCT_VERSION, DEFAULT_TOOLKIT_REVISION


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FailureMode(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    REJECT = "reject row"
    FAIL = "fail build"


class ModelLayer(StrEnum):
    STAGING = "staging"
    INTERMEDIATE = "intermediate"
    MART = "mart"


class Materialization(StrEnum):
    VIEW = "view"
    TABLE = "table"
    INCREMENTAL = "incremental"
    EPHEMERAL = "ephemeral"


class JoinType(StrEnum):
    LEFT = "left"
    INNER = "inner"
    RIGHT = "right"
    FULL = "full"


class Cardinality(StrEnum):
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_ONE = "many-to-one"
    MANY_TO_MANY = "many-to-many"


class SchemaImplementation(StrEnum):
    MAPPED = "mapped"
    AUDIT = "audit"
    SYSTEM_GENERATED = "system-generated"


class ProductMetadata(StrictModel):
    contract_id: str | None = None
    product_id: str
    name: str
    version: str = DEFAULT_DATA_PRODUCT_VERSION
    status: str = "draft"
    domain: str | None = None
    description: str | None = None
    owner: str | None = None
    owner_email: str | None = None


class SchemaProperty(StrictModel):
    object_name: str
    name: str
    logical_type: str
    physical_type: str | None = None
    description: str | None = None
    required: bool = False
    primary_key: bool = False
    unique: bool = False
    classification: str | None = None
    implementation: SchemaImplementation = SchemaImplementation.MAPPED
    workbook_sheet: str | None = None
    workbook_row: int | None = None
    odcs_fields: dict[str, JsonValue] = Field(default_factory=dict)


class SourceSpecification(StrictModel):
    relation: str
    source_name: str
    table_name: str
    database: str | None = None
    schema_name: str | None = None
    description: str | None = None


class SourceColumn(StrictModel):
    relation: str
    name: str
    logical_type: str
    physical_type: str | None = None
    nullable: bool = True
    unique: bool = False
    description: str | None = None
    workbook_row: int


class ModelSpecification(StrictModel):
    name: str
    layer: ModelLayer
    materialization: Materialization = Materialization.VIEW
    description: str | None = None
    grain: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    audit_source: str | None = None
    incremental_strategy: str | None = None
    enforce_contract: bool = False
    enabled: bool = True


class TransformationStep(StrictModel):
    step: int = Field(ge=1)
    operation: str
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    workbook_row: int


class ColumnMapping(StrictModel):
    model: str
    target_field: str
    source_relation: str
    source_field: str
    source_type: str
    steps: list[TransformationStep] = Field(default_factory=list)

    @field_validator("steps")
    @classmethod
    def steps_are_ordered(cls, value: list[TransformationStep]) -> list[TransformationStep]:
        return sorted(value, key=lambda item: item.step)


class ValidationRule(StrictModel):
    model: str
    name: str
    target_field: str
    operation: str
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    failure: FailureMode
    description: str | None = None
    workbook_row: int


class LookupEntry(StrictModel):
    lookup: str
    source_value: str
    target_value: JsonValue
    workbook_row: int


class Relationship(StrictModel):
    model: str
    left_relation: str
    right_relation: str
    join_type: JoinType
    left_key: str
    right_key: str
    cardinality: Cardinality
    workbook_row: int


class Server(StrictModel):
    name: str
    server_type: str
    environment: str
    account: str | None = None
    database: str | None = None
    schema_name: str | None = None
    host: str | None = None
    port: int | None = None


class TeamMember(StrictModel):
    username: str
    name: str | None = None
    role: str | None = None
    email: str | None = None


class SlaProperty(StrictModel):
    name: str
    value: JsonValue
    unit: str | None = None
    description: str | None = None


class ContractQualityRule(StrictModel):
    object_name: str
    property_name: str | None = None
    rule_id: str
    rule_type: str = "library"
    metric: str | None = None
    threshold: str | None = None
    value: JsonValue = None
    dimension: str | None = None
    description: str | None = None
    query: str | None = None
    engine: str | None = None
    implementation: JsonValue = None
    severity: str | None = None
    scheduler: str | None = None
    schedule: str | None = None
    odcs_fields: dict[str, JsonValue] = Field(default_factory=dict)
    workbook_sheet: str = "Quality"
    workbook_row: int


class BuildConfiguration(StrictModel):
    adapter: str = "duckdb"
    profile: str = "generated_data_product"
    target_schema: str = "main"
    toolkit_git_env: str = "DBT_DATA_ENGINEERING_TOOLKIT_GIT_URL"
    toolkit_revision: str = DEFAULT_TOOLKIT_REVISION
    allow_many_to_many: bool = False
    contract_test_authority: str = "datacontract"


class Role(StrictModel):
    role: str
    description: str | None = None
    access: str | None = None


class SupportChannel(StrictModel):
    channel: str
    url: str | None = None
    description: str | None = None


class DataProductSpecification(StrictModel):
    metadata: ProductMetadata
    schema_properties: list[SchemaProperty] = Field(default_factory=list)
    sources: list[SourceSpecification] = Field(default_factory=list)
    source_columns: list[SourceColumn] = Field(default_factory=list)
    models: list[ModelSpecification] = Field(default_factory=list)
    mappings: list[ColumnMapping] = Field(default_factory=list)
    rules: list[ValidationRule] = Field(default_factory=list)
    lookups: list[LookupEntry] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    servers: list[Server] = Field(default_factory=list)
    team: list[TeamMember] = Field(default_factory=list)
    sla: list[SlaProperty] = Field(default_factory=list)
    quality: list[ContractQualityRule] = Field(default_factory=list)
    roles: list[Role] = Field(default_factory=list)
    support: list[SupportChannel] = Field(default_factory=list)
    odcs_passthrough: dict[str, JsonValue] = Field(default_factory=dict)
    build: BuildConfiguration = Field(default_factory=BuildConfiguration)

    def model(self, name: str) -> ModelSpecification:
        return next(item for item in self.models if item.name == name)

    def lookup(self, name: str) -> dict[str, JsonValue]:
        return {
            item.source_value: item.target_value for item in self.lookups if item.lookup == name
        }

    def source_column(self, relation: str, name: str) -> SourceColumn | None:
        return next(
            (
                item
                for item in self.source_columns
                if item.relation == relation and item.name == name
            ),
            None,
        )
