const CredentialFilterFields = [
  {
    id: 'name',
    title: 'Name',
    placeholder: 'Filter by Name',
    filterType: 'text'
  },
  {
    id: 'credentialType',
    title: 'Credential Type',
    placeholder: 'Filter by Credential Type',
    filterType: 'select',
    filterValues: [
      { title: 'Network', id: 'network' },
      { title: 'Satellite', id: 'satellite' },
      { title: 'VCenter', id: 'vcenter' }
    ]
  },
  {
    id: 'authenticationType',
    title: 'Authentication Type',
    placeholder: 'Filter by Authentication Type',
    filterType: 'select',
    filterValues: [
      { title: 'SSH Key', id: 'sshKey' },
      { title: 'Username & Password', id: 'usernamePassword' },
      { title: 'Become User', id: 'becomeUser' }
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
