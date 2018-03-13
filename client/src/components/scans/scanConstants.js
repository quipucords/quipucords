const ScanFilterFields = [];

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
