from base_fhirpy import Client, SearchSet, Resource, Reference

__title__ = 'aidbox-py'
__version__ = '0.0.1'
__author__ = 'beda.software'
__license__ = 'None'
__copyright__ = 'Copyright 2019 beda.software'

# Version synonym
VERSION = __version__


class AidboxSearchSet(SearchSet):
    pass


class AidboxResource(Resource):
    def is_reference(self, value):
        if not isinstance(value, dict):
            return False

        return 'resourceType' in value and ('id' in value or 'url' in value) and \
               not (set(value.keys()) - {'resourceType', 'id', '_id', 'resource', 'display', 'url'})

    @property
    def id(self):
        return self.get('id', None)

    @property
    def reference(self):
        """
        Returns reference if local resource is saved
        """
        if self.id:
            return '{0}/{1}'.format(self.resource_type, self.id)


class AidboxReference(Reference):
    def get_root_keys(self):
        return ['resourceType', 'id', 'display', 'url', 'resource']

    @property
    def reference(self):
        """
        Returns reference if local resource is saved
        """
        if self.is_local:
            return '{0}/{1}'.format(self.resource_type, self.id)
        return self.get('url', None)

    @property
    def id(self):
        if self.is_local:
            return self.get('id', None)

    @property
    def resource_type(self):
        """
        Returns resource type if reference specifies to the local resource
        """
        if self.is_local:
            return self.get('resourceType', None)

    @property
    def is_local(self):
        return not self.get('url')


class AidboxClient(Client):
    searchset_class = AidboxSearchSet
    resource_class = AidboxResource

    def reference(self, resource_type=None, id=None, reference=None, **kwargs):
        resource_type = kwargs.pop('resourceType', resource_type)
        if reference:
            if reference.count('/') > 1:
                return AidboxReference(self, url=reference, **kwargs)
            resource_type, id = reference.split('/')
        if not resource_type and not id:
            raise TypeError(
                'Arguments `resource_type` and `id` or `reference`'
                'are required')
        return AidboxReference(self, resourceType=resource_type, id=id, **kwargs)
