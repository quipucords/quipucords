const CredentialFilterFields = [
  {
    id: 'search_by_name',
    title: 'Name',
    placeholder: 'Filter by Name',
    filterType: 'text'
  },
  {
    id: 'cred_type',
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

/**
 * ID: Enum with the following possible values [name, cred_type]
 */
const CredentialSortFields = [
  {
    id: 'name',
    title: 'Name',
    isNumeric: false
  },
  {
    id: 'cred_type',
    title: 'Credential Type',
    isNumeric: false
  }
];

export { CredentialFilterFields, CredentialSortFields };
