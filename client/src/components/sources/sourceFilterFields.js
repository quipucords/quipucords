export const SourceFilterFields = [
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
      { title: 'VCenter', id: 'vcenter' }
    ]
  }
];
