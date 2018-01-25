const CredentialFilterFields = [
  {
    id: 'name',
    title: 'Name',
    placeholder: 'Filter by Name',
    filterType: 'text'
  },
  {
    id: 'sourceType',
    title: 'Source Type',
    placeholder: 'Filter by Source Type',
    filterType: 'select',
    filterValues: [
      { title: 'Network', id: 'network' },
      { title: 'Satellite', id: 'satellite' },
      { title: 'VCenter', id: 'vcenter' }
    ]
  },
  {
    id: 'credentialType',
    title: 'Credential Type',
    placeholder: 'Filter by Credential Type',
    filterType: 'select',
    filterValues: [
      { title: 'SSH Key', id: 'sshKey' },
      { title: 'Username & Password', id: 'usernamePassword' }
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
    id: 'sourceType',
    title: 'Source Type',
    isNumeric: false
  },
  {
    id: 'credentialType',
    title: 'Credential Type',
    isNumeric: false
  }
];

export { CredentialFilterFields, CredentialSortFields };
