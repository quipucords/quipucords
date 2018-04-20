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

/**
 * ID: Enum with the following possible values [id, name, scan_type, most_recent_scanjob__start_time, most_recent_scanjob__status]
 */
const ScanSortFields = [
  {
    id: 'name',
    title: 'Name',
    isNumeric: false
  },
  {
    id: 'most_recent_scanjob__start_time',
    title: 'Most Recent',
    isNumeric: true,
    sortAscending: false
  }
];

export { ScanFilterFields, ScanSortFields };
