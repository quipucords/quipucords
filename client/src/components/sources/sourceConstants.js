const SourceFilterFields = [
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

const SourceSortFields = [
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
    id: 'hostCount',
    title: 'Hosts Count',
    isNumeric: true
  }
];

export { SourceFilterFields, SourceSortFields };
