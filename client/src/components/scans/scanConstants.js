const ScanFilterFields = [
  {
    id: 'search_by_name',
    title: 'Name',
    placeholder: 'Filter by Name',
    filterType: 'text'
  },
  {
    id: 'search_sources_by_name',
    title: 'Source',
    placeholder: 'Filter by Source Name',
    filterType: 'text'
  }
];

const ScanSortFields = [
  {
    id: 'name',
    title: 'Name',
    isNumeric: false
  },
  {
    id: 'most_recent_scanjob__start_time',
    title: 'Most Recent Time',
    isNumeric: true
  }
];

export { ScanFilterFields, ScanSortFields };
