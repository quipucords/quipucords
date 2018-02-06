import { helpers } from '../../common/helpers';

const ScanFilterFields = [
  {
    id: 'name',
    title: 'Name',
    placeholder: 'Filter by Name',
    filterType: 'text'
  },
  {
    id: 'source',
    title: 'Source',
    placeholder: 'Filter by Source',
    filterType: 'text'
  },
  {
    id: 'status',
    title: 'Status',
    placeholder: 'Filter by Status',
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
  }
];

const ScanSortFields = [
  {
    id: 'name',
    title: 'Name',
    isNumeric: false
  },
  {
    id: 'status',
    title: 'Status',
    isNumeric: false
  },
  {
    id: 'time',
    title: 'Time',
    isNumeric: true
  },
  {
    id: 'hostCount',
    title: 'System Count',
    isNumeric: true
  },
  {
    id: 'successfulHosts',
    title: 'Successful System Scans',
    isNumeric: true
  },
  {
    id: 'failedHosts',
    title: 'Failed System Scans',
    isNumeric: true
  },
  {
    id: 'sourceCount',
    title: 'Sources Count',
    isNumeric: true
  },
  {
    id: 'scansCount',
    title: 'Scans Count',
    isNumeric: true
  }
];

export { ScanFilterFields, ScanSortFields };
