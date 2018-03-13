import { helpers } from '../../common/helpers';
const SourceFilterFields = [
  {
    id: 'source_type',
    title: 'Source Type',
    placeholder: 'Filter by Source Type',
    filterType: 'select',
    filterValues: [
      { title: helpers.sourceTypeString('network'), id: 'network' },
      { title: helpers.sourceTypeString('satellite'), id: 'satellite' },
      { title: helpers.sourceTypeString('vcenter'), id: 'vcenter' }
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
    id: 'source_type',
    title: 'Source Type',
    isNumeric: false
  },
  {
    id: 'most_recent_connect_scan__start_time',
    title: 'Most Recent Connection Scan',
    isNumeric: true
  }
];

export { SourceFilterFields, SourceSortFields };
