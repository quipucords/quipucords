import { dictionary } from '../../constants/dictionaryConstants';

const SourceFilterFields = [
  {
    id: 'search_by_name',
    title: 'Name',
    placeholder: 'Filter by Name',
    filterType: 'text'
  },
  {
    id: 'search_credentials_by_name',
    title: 'Credential',
    placeholder: 'Filter by Credential Name',
    filterType: 'text'
  },
  {
    id: 'source_type',
    title: 'Source Type',
    placeholder: 'Filter by Source Type',
    filterType: 'select',
    filterValues: [
      { title: dictionary.network, id: 'network' },
      { title: dictionary.satellite, id: 'satellite' },
      { title: dictionary.vcenter, id: 'vcenter' }
    ]
  }
];

/**
 * ID: Enum with the following possible values [name, source_type, most_recent_connect_scan__start_time]
 */
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
    title: 'Most Recent',
    isNumeric: true,
    sortAscending: false
  }
];

export { SourceFilterFields, SourceSortFields };
