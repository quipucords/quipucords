import { helpers } from '../../common/helpers';
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
      { title: helpers.sourceTypeString('network'), id: 'network' },
      { title: helpers.sourceTypeString('satellite'), id: 'satellite' },
      { title: helpers.sourceTypeString('vcenter'), id: 'vcenter' }
    ]
  },
  {
    id: 'hosts',
    title: 'IP Address',
    placeholder: 'Filter by IP Address',
    filterType: 'text'
  },
  {
    id: 'status',
    title: 'Connection Status',
    placeholder: 'Filter by connection status',
    filterType: 'select',
    filterValues: [
      { title: helpers.scanStatusString('completed'), id: 'completed' },
      { title: helpers.scanStatusString('failed'), id: 'failed' },
      { title: helpers.scanStatusString('created'), id: 'created' },
      { title: helpers.scanStatusString('running'), id: 'running' },
      { title: helpers.scanStatusString('paused'), id: 'paused' },
      { title: helpers.scanStatusString('pending'), id: 'pending' },
      { title: helpers.scanStatusString('canceled'), id: 'canceled' }
    ]
  },
  {
    id: 'credentials',
    title: 'Credentials',
    placeholder: 'Filter by Credentials',
    filterType: 'text'
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
    id: 'status',
    title: 'Connection Status',
    isNumeric: false
  },
  {
    id: 'credentialsCount',
    title: 'Credentials Count',
    isNumeric: true
  },
  {
    id: 'hostCount',
    title: 'Systems Count',
    isNumeric: true
  },
  {
    id: 'successHostCount',
    title: 'Successful Authentications',
    isNumeric: true
  },
  {
    id: 'failedHostCount',
    title: 'Failed Authentications',
    isNumeric: true
  }
];

export { SourceFilterFields, SourceSortFields };
