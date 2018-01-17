const ScanFilterFields = [
  {
    id: 'status',
    title: 'Status',
    placeholder: 'Filter by Status',
    filterType: 'select',
    filterValues: [
      { title: 'Completed', id: 'completed' },
      { title: 'Failed', id: 'failed' },
      { title: 'Created', id: 'created' },
      { title: 'Running', id: 'running' },
      { title: 'Paused', id: 'paused' },
      { title: 'Pending', id: 'pending' },
      { title: 'Canceled', id: 'canceled' }
    ]
  },
  {
    id: 'scanType',
    title: 'Scan Type',
    placeholder: 'Filter by Scan Type',
    filterType: 'select',
    filterValues: [
      { title: 'Connect', id: 'connect' },
      { title: 'Inspect', id: 'inspect' }
    ]
  },
  {
    id: 'source',
    title: 'Source',
    placeholder: 'Filter by sources',
    filterType: 'text'
  }
];

const ScanSortFields = [
  {
    id: 'status',
    title: 'Status',
    isNumeric: false
  },
  {
    id: 'scanType',
    title: 'Scan Type',
    isNumeric: false
  },
  {
    id: 'sourceCount',
    title: 'Sources Count',
    isNumeric: true
  }
];

export { ScanFilterFields, ScanSortFields };
