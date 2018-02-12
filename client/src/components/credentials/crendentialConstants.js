const CredentialFilterFields = [
  {
    id: 'name',
    title: 'Name',
    placeholder: 'Filter by Name',
    filterType: 'text'
  },
  {
    id: 'source_type',
    title: 'Credential Type',
    placeholder: 'Filter by Credential Type',
    filterType: 'select',
    filterValues: [
      { title: 'Network', id: 'network' },
      { title: 'Satellite', id: 'satellite' },
      { title: 'VCenter', id: 'vcenter' }
    ]
  }
];

const CredentialSortFields = [
  {
    id: 'name',
    title: 'Name',
    isNumeric: false
  },
  {
    id: 'credentialType',
    title: 'Credential Type',
    isNumeric: false
  },
  {
    id: 'authenticationType',
    title: 'Authentication Type',
    isNumeric: false
  }
];

export { CredentialFilterFields, CredentialSortFields };
