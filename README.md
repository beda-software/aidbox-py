[![Build Status](https://travis-ci.org/beda-software/aidbox-py.svg?branch=master)](https://travis-ci.org/beda-software/aidbox-py)
[![codecov](https://codecov.io/gh/beda-software/aidbox-py/branch/master/graph/badge.svg)](https://codecov.io/gh/beda-software/aidbox-py)
[![pypi](https://img.shields.io/pypi/v/aidbox.svg)](https://pypi.python.org/pypi/aidbox)

# aidbox-py
Aidbox client for python.
This package provides an API for CRUD operations over Aidbox resources.

The library is based on [fhir-py](https://github.com/beda-software/fhir-py) and the main difference between libraries in our case is the way they represent resource references (read more about [differences](https://docs.aidbox.app/basic-concepts/aidbox-and-fhir-formats)).

Aidbox-py also going to support some Aidbox features like _assoc operation, AidboxQuery and so on.

Most examples from [fhir-py readme](https://github.com/beda-software/fhir-py/blob/master/README.md) also work for aidbox-py (but you need to replace FHIR client with AsyncAidboxClient/SyncAidboxClient). See base aidbox-py example below.


# Getting started
## Install
Most recent version:
`pip install git+https://github.com/beda-software/aidbox-py.git`
PyPi:
`pip install aidbox`

## Async example
```Python
import asyncio
from aidboxpy import AsyncAidboxClient
from fhirpy.base.exceptions import (
    OperationOutcome, ResourceNotFound, MultipleResourcesFound
)


async def main():
    # Create an instance
    client = AsyncAidboxClient(
        'http://localhost:8080',
        authorization='Bearer TOKEN'
    )

    # Search for patients
    resources = client.resources('Patient')  # Return lazy search set
    resources = resources.search(name='John').limit(10).page(2).sort('name')
    patients = await resources.fetch()  # Returns a list of AsyncAidboxResource

    # Get exactly one resource
    try:
        patient = await client.resources('Practitioner') \
            .search(id='id').get()
    except ResourceNotFound:
        pass
    except MultipleResourcesFound:
        pass

    # Validate resource
    try:
        await client.resource(
            'Person',
            custom_prop='123',
            telecom=True
        ).is_valid()
    except OperationOutcome as e:
        print('Error: {}'.format(e))

    # Create Organization resource
    organization = client.resource(
        'Organization',
        name='beda.software',
        active=False
    )
    await organization.save()

    # Get patient resource by reference and delete
    patient_ref = client.reference('Patient', 'new_patient')
    patient_res = await patient_ref.to_resource()
    await patient_res.delete()

    # Iterate over search set and change organization
    org_resources = client.resources('Organization').search(active=False)
    async for org_resource in org_resources:
        org_resource['active'] = True
        await org_resource.save()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```


# API
Import library:

`from aidboxpy import SyncAidboxClient`

or

`from aidboxpy import AsyncAidboxClient`

To create AidboxClient instance use:

`SyncAidboxClient(url, authorization='', extra_headers={})`

or

`AsyncAidboxClient(url, authorization='', extra_headers={})`

Returns an instance of the connection to the server which provides:
* .reference(resource_type, id, reference, **kwargs) - returns `SyncAidboxReference`/`AsyncAidboxReference` to the resource
* .resource(resource_type, **kwargs) - returns `SyncAidboxResource`/`AsyncAidboxResource` which described below
* .resources(resource_type) - returns `SyncAidboxSearchSet`/`AsyncAidboxSearchSet`

`SyncAidboxResource`/`AsyncAidboxResource`

provides:
* .serialize() - serializes resource
* .get_by_path(path, default=None) – gets the value at path of resource
* .save() - creates or updates resource instance
* .delete() - deletes resource instance
* .to_reference(**kwargs) - returns  `SyncAidboxReference`/`AsyncAidboxReference` for this resource

`SyncAidboxReference`/`AsyncAidboxReference`

provides:
* .to_resource() - returns `SyncAidboxResource`/`AsyncAidboxResource` for this reference

`SyncAidboxSearchSet`/`AsyncAidboxSearchSet`

provides:
* .search(param=value)
* .limit(count)
* .page(page)
* .sort(*args)
* .elements(*args, exclude=False)
* .include(resource_type, attr=None, recursive=False, iterate=False)
* .revinclude(resource_type, attr=None, recursive=False, iterate=False)
* .has(*args, **kwargs)
* .assoc(elements)
* `async` .fetch() - makes query to the server and returns a list of `Resource` filtered by resource type
* `async` .fetch_all() - makes query to the server and returns a full list of `Resource` filtered by resource type
* `async` .fetch_raw() - makes query to the server and returns a raw Bundle `Resource`
* `async` .first() - returns `Resource` or None
* `async` .get(id=None) - returns `Resource` or raises `ResourceNotFound` when no resource found or MultipleResourcesFound when more than one resource found (parameter 'id' is deprecated)
* `async` .count() - makes query to the server and returns the total number of resources that match the SearchSet
