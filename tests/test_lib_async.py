import pytest
from aiohttp import BasicAuth

from aidboxpy import AsyncAidboxClient
from aidboxpy import AsyncAidboxReference, AsyncAidboxResource
from fhirpy.base.exceptions import (
    ResourceNotFound,
    OperationOutcome,
    MultipleResourcesFound,
)
from fhirpy.base.utils import AttrDict


class TestLibAsyncCase(object):
    URL = "http://localhost:8080"
    client = None
    identifier = [{"system": "http://example.com/env", "value": "fhirpy"}]

    @classmethod
    def get_search_set(cls, resource_type):
        return cls.client.resources(resource_type).search(**{"identifier": "fhirpy"})

    @pytest.fixture(autouse=True)
    @pytest.mark.asyncio
    async def clearDb(self):
        for resource_type in ["Patient", "Practitioner"]:
            search_set = self.get_search_set(resource_type)
            async for item in search_set:
                await item.delete()

    @classmethod
    def setup_class(cls):
        cls.client = AsyncAidboxClient(
            cls.URL, authorization=BasicAuth("root", "secret").encode()
        )

    async def create_resource(self, resource_type, **kwargs):
        p = self.client.resource(resource_type, identifier=self.identifier, **kwargs)
        await p.save()

        return p

    @pytest.mark.asyncio
    async def test_create_patient(self):
        await self.create_resource(
            "Patient", id="patient", name=[{"text": "My patient"}]
        )

        patient = await self.client.resources("Patient").search(id="patient").get()
        assert patient["name"] == [{"text": "My patient"}]

    @pytest.mark.asyncio
    async def test_update_patient(self):
        patient = await self.create_resource(
            "Patient", id="patient", name=[{"text": "My patient"}]
        )
        patient["active"] = True
        patient.birthDate = "1945-01-12"
        patient.name[0].text = "SomeName"
        await patient.save()

        check_patient = (
            await self.client.resources("Patient").search(id="patient").get()
        )
        assert check_patient.active is True
        assert check_patient["birthDate"] == "1945-01-12"
        assert check_patient.get_by_path(["name", 0, "text"]) == "SomeName"

    @pytest.mark.asyncio
    async def test_count(self):
        search_set = self.get_search_set("Patient")

        assert await search_set.count() == 0

        await self.create_resource(
            "Patient", id="patient1", name=[{"text": "John Smith FHIRPy"}]
        )

        assert await search_set.count() == 1

    @pytest.mark.asyncio
    async def test_create_without_id(self):
        patient = await self.create_resource("Patient")

        assert patient.id is not None

    @pytest.mark.asyncio
    async def test_delete(self):
        patient = await self.create_resource("Patient", id="patient")
        await patient.delete()

        with pytest.raises(ResourceNotFound):
            await self.get_search_set("Patient").search(id="patient").get()

    @pytest.mark.asyncio
    async def test_get_not_existing_id(self):
        with pytest.raises(ResourceNotFound):
            await self.client.resources("Patient").get(id="FHIRPypy_not_existing_id")

    @pytest.mark.asyncio
    async def test_get_more_than_one_resources(self):
        await self.create_resource("Patient", birthDate="1901-05-25")
        await self.create_resource("Patient", birthDate="1905-05-25")
        with pytest.raises(MultipleResourcesFound):
            await self.client.resources("Patient").get()
        with pytest.raises(MultipleResourcesFound):
            await self.client.resources("Patient").search(birthdate__gt="1900").get()

    @pytest.mark.asyncio
    async def test_get_resource_by_id_is_deprecated(self):
        await self.create_resource("Patient", id="patient", gender="male")
        with pytest.warns(DeprecationWarning):
            patient = (
                await self.client.resources("Patient")
                .search(gender="male")
                .get(id="patient")
            )
        assert patient.id == "patient"

    @pytest.mark.asyncio
    async def test_get_resource_by_search_with_id(self):
        await self.create_resource("Patient", id="patient", gender="male")
        patient = (
            await self.client.resources("Patient")
            .search(gender="male", id="patient")
            .get()
        )
        assert patient.id == "patient"
        with pytest.raises(ResourceNotFound):
            await self.client.resources("Patient").search(
                gender="female", id="patient"
            ).get()

    @pytest.mark.asyncio
    async def test_get_resource_by_search(self):
        await self.create_resource(
            "Patient", id="patient1", gender="male", birthDate="1901-05-25"
        )
        await self.create_resource(
            "Patient", id="patient2", gender="female", birthDate="1905-05-25"
        )
        patient_1 = (
            await self.client.resources("Patient")
            .search(gender="male", birthdate="1901-05-25")
            .get()
        )
        assert patient_1.id == "patient1"
        patient_2 = (
            await self.client.resources("Patient")
            .search(gender="female", birthdate="1905-05-25")
            .get()
        )
        assert patient_2.id == "patient2"

    def test_resource_without_resource_type_failed(self):
        with pytest.raises(TypeError):
            self.client.resource()

    def test_resource_success(self):
        resource = self.client.resource("Patient", id="p1")
        assert resource.resource_type == "Patient"
        assert resource["resourceType"] == "Patient"
        assert resource.id == "p1"
        assert resource["id"] == "p1"
        assert resource.reference == "Patient/p1"
        assert resource.serialize() == {
            "resourceType": "Patient",
            "id": "p1",
        }

    def test_reference_from_external_reference(self):
        reference = self.client.reference(reference="http://external.com/Patient/p1")
        assert reference.is_local is False
        assert reference.resource_type is None
        assert reference.id is None
        assert reference.reference == "http://external.com/Patient/p1"
        assert reference["url"] == "http://external.com/Patient/p1"
        assert reference.serialize() == {"url": "http://external.com/Patient/p1"}

    def test_reference_from_resource_type_and_id(self):
        reference = self.client.reference("Patient", "p1")
        assert reference.resource_type == "Patient"
        assert reference.id == "p1"
        assert reference.reference == "Patient/p1"
        assert reference.get("url") is None
        assert reference.serialize() == {"resourceType": "Patient", "id": "p1"}

    def test_reference_from_local_reference(self):
        reference = self.client.reference(reference="Patient/p1")
        assert reference.resource_type == "Patient"
        assert reference.id == "p1"
        assert reference.reference == "Patient/p1"
        assert reference.get("url") is None
        assert reference.serialize() == {"resourceType": "Patient", "id": "p1"}

    @pytest.mark.asyncio
    async def test_not_found_error(self):
        with pytest.raises(ResourceNotFound):
            await self.client.resources("FHIRPyNotExistingResource").fetch()

    @pytest.mark.asyncio
    async def test_operation_outcome_error(self):
        with pytest.raises(OperationOutcome):
            await self.create_resource("Patient", name="invalid")

    @pytest.mark.asyncio
    async def test_to_resource_for_local_reference(self):
        await self.create_resource("Patient", id="p1", name=[{"text": "Name"}])

        patient_ref = self.client.reference("Patient", "p1")
        result = (await patient_ref.to_resource()).serialize()
        result.pop("meta")
        result.pop("identifier")

        assert result == {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"text": "Name"}],
        }

    @pytest.mark.asyncio
    async def test_to_resource_for_external_reference(self):
        reference = self.client.reference(reference="http://external.com/Patient/p1")

        with pytest.raises(ResourceNotFound):
            await reference.to_resource()

    @pytest.mark.asyncio
    async def test_to_resource_for_resource(self):
        resource = self.client.resource("Patient", id="p1", name=[{"text": "Name"}])
        resource_copy = await resource.to_resource()
        assert isinstance(resource_copy, AsyncAidboxResource)
        assert resource_copy.serialize() == {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"text": "Name"}],
        }

    def test_to_reference_for_resource_without_id(self):
        resource = self.client.resource("Patient")
        with pytest.raises(ResourceNotFound):
            resource.to_reference()

    @pytest.mark.asyncio
    async def test_to_reference_for_resource(self):
        patient = await self.create_resource("Patient", id="p1")

        assert patient.to_reference().serialize() == {
            "resourceType": "Patient",
            "id": "p1",
        }

        assert patient.to_reference(display="patient").serialize() == {
            "resourceType": "Patient",
            "id": "p1",
            "display": "patient",
        }

    def test_to_reference_for_reference(self):
        reference = self.client.reference("Patient", "p1")
        reference_copy = reference.to_reference(display="patient")
        assert isinstance(reference_copy, AsyncAidboxReference)
        assert reference_copy.serialize() == {
            "resourceType": "Patient",
            "id": "p1",
            "display": "patient",
        }

    def test_serialize(self):
        practitioner1 = self.client.resource("Practitioner", id="pr1")
        practitioner2 = self.client.resource("Practitioner", id="pr2")
        patient = self.client.resource(
            "Patient",
            id="patient",
            generalPractitioner=[
                practitioner1.to_reference(display="practitioner"),
                practitioner2,
            ],
        )

        assert patient.serialize() == {
            "resourceType": "Patient",
            "id": "patient",
            "generalPractitioner": [
                {
                    "resourceType": "Practitioner",
                    "id": "pr1",
                    "display": "practitioner",
                },
                {
                    "resourceType": "Practitioner",
                    "id": "pr2",
                },
            ],
        }

    def test_equality(self):
        resource = self.client.resource("Patient", id="p1")
        reference = self.client.reference("Patient", "p1")
        assert resource == reference

    def test_bundle_path(self):
        bundle_resource = self.client.resource("Bundle")
        assert bundle_resource._get_path() == ""

    @pytest.mark.asyncio
    async def test_create_bundle(self):
        bundle = {
            "resourceType": "bundle",
            "type": "transaction",
            "entry": [
                {
                    "request": {"method": "POST", "url": "/Patient"},
                    "resource": {
                        "id": "bundle_patient_1",
                        "identifier": self.identifier,
                    },
                },
                {
                    "request": {"method": "POST", "url": "/Patient"},
                    "resource": {
                        "id": "bundle_patient_2",
                        "identifier": self.identifier,
                    },
                },
            ],
        }
        bundle_resource = await self.create_resource("Bundle", **bundle)
        patient_1 = (
            await self.client.resources("Patient").search(id="bundle_patient_1").get()
        )
        patient_2 = (
            await self.client.resources("Patient").search(id="bundle_patient_2").get()
        )

    @pytest.mark.asyncio
    async def test_is_valid(self):
        resource = self.client.resource
        assert await resource("Patient", id="id123").is_valid() is True
        assert (
            await resource("Patient", gender="female").is_valid(raise_exception=True)
            is True
        )

        assert await resource("Patient", gender=True).is_valid() is False
        with pytest.raises(OperationOutcome):
            await resource("Patient", gender=True).is_valid(raise_exception=True)

        assert (
            await resource("Patient", gender="female", custom_prop="123").is_valid()
            is False
        )
        with pytest.raises(OperationOutcome):
            await resource("Patient", gender="female", custom_prop="123").is_valid(
                raise_exception=True
            )

        assert (
            await resource("Patient", gender="female", custom_prop="123").is_valid()
            is False
        )
        with pytest.raises(OperationOutcome):
            await resource(
                "Patient", birthDate="date", custom_prop="123", telecom=True
            ).is_valid(raise_exception=True)

    @pytest.mark.asyncio
    async def test_references_after_save(self):
        patient = await self.create_resource("Patient", name=[{"text": "John First"}])
        practitioner = await self.create_resource(
            "Practitioner", name=[{"text": "Jack"}]
        )
        appointment = self.client.resource(
            "Appointment",
            **{
                "status": "booked",
                "participant": [
                    {"actor": patient, "status": "accepted"},
                    {"actor": practitioner, "status": "accepted"},
                ],
            },
        )
        await appointment.save()
        assert isinstance(appointment.participant[0].actor, AsyncAidboxReference)
        assert isinstance(appointment.participant[0], AttrDict)
        test_patient = await appointment.participant[0].actor.to_resource()
        assert test_patient

        assert isinstance(appointment.participant[1].actor, AsyncAidboxReference)
        assert isinstance(appointment.participant[1], AttrDict)
        test_practitioner = await appointment.participant[1].actor.to_resource()
        assert test_practitioner

    @pytest.mark.asyncio
    async def test_resource_execute_mapping_debug(self):
        """
        Specific Aidbox operation (https://docs.aidbox.app/integrations/mappings)
        """
        mapping = self.client.resource(
            "Mapping",
            body={
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [
                    {
                        "request": {"url": "/fhir/Patient", "method": "POST"},
                        "resource": {
                            "resourceType": "Patient",
                            "name": [
                                {"given": ["$ firstName"], "family": "$ lastName"}
                            ],
                        },
                    }
                ],
            },
        )
        await mapping.save()
        response = await mapping.execute(
            "$debug", data={"firstName": "John", "lastName": "Smith"}
        )
        assert response["resourceType"] == "Bundle"
        assert response["type"] == "transaction"
        assert response["entry"][0]["request"] == mapping["body"]["entry"][0]["request"]
        assert response["entry"][0]["resource"] == {
            "resourceType": "Patient",
            "name": [{"given": ["John"], "family": "Smith"}],
        }

    @pytest.mark.asyncio
    async def test_client_execute_mapping_debug(self):
        """
        Specific Aidbox operation (https://docs.aidbox.app/integrations/mappings)
        """
        mapping = {
            "body": {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [
                    {
                        "request": {"url": "/fhir/Patient", "method": "POST"},
                        "resource": {
                            "resourceType": "Patient",
                            "name": [
                                {"given": ["$ firstName"], "family": "$ lastName"}
                            ],
                        },
                    }
                ],
            }
        }
        response = await self.client.execute(
            f"Mapping/$debug",
            data={
                "mapping": mapping,
                "scope": {"firstName": "John", "lastName": "Smith"},
            },
        )
        assert response["resourceType"] == "Bundle"
        assert response["type"] == "transaction"
        assert response["entry"][0]["request"] == mapping["body"]["entry"][0]["request"]
        assert response["entry"][0]["resource"] == {
            "resourceType": "Patient",
            "name": [{"given": ["John"], "family": "Smith"}],
        }
