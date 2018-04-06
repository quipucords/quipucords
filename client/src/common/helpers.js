import _ from 'lodash';

const bindMethods = (context, methods) => {
  methods.forEach(method => {
    context[method] = context[method].bind(context);
  });
};

const devModeNormalizeCount = (count, modulus = 100) => Math.abs(count) % modulus;

const generateId = prefix => `${prefix || 'generatedid'}-${Math.ceil(1e5 * Math.random())}`;

const noop = Function.prototype;

const sourceTypeString = sourceType => {
  switch (sourceType) {
    case 'vcenter':
      return 'VCenter';
    case 'network':
      return 'Network';
    case 'satellite':
      return 'Satellite';
    default:
      return '';
  }
};

const sourceTypeIcon = sourceType => {
  switch (sourceType) {
    case 'vcenter':
      return { type: 'pf', name: 'vcenter' };
    case 'network':
      return { type: 'pf', name: 'network-range' };
    case 'satellite':
      return { type: 'pf', name: 'satellite' };
    default:
      return { type: 'pf', name: '' };
  }
};

const scanTypeString = scanType => {
  switch (scanType) {
    case 'connect':
      return 'Connection Scan';
    case 'inspect':
      return 'Inspection Scan';
    default:
      return '';
  }
};

const scanTypeIcon = scanType => {
  switch (scanType) {
    case 'connect':
      return { type: 'pf', name: 'connected' };
    case 'inspect':
      return { type: 'fa', name: 'search' };
    default:
      return { type: 'pf', name: '' };
  }
};

const scanStatusString = scanStatus => {
  switch (scanStatus) {
    case 'success':
      return 'Successful';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    case 'created':
      return 'Created';
    case 'running':
      return 'Running';
    case 'paused':
      return 'Paused';
    case 'pending':
      return 'Pending';
    case 'canceled':
      return 'Canceled';
    default:
      console.error(`Unknown status: ${scanStatus}`);
      return '';
  }
};

const scanStatusIcon = scanStatus => {
  switch (scanStatus) {
    case 'completed':
    case 'success':
      return { type: 'pf', name: 'ok', classNames: [] };
    case 'failed':
    case 'canceled':
      return { type: 'pf', name: 'error-circle-o', classNames: [] };
    case 'unreachable':
      return { type: 'pf', name: 'disconnected', classNames: ['is-error'] };
    case 'created':
    case 'pending':
    case 'running':
      return { type: 'fa', name: 'spinner', classNames: ['fa-spin'] };
    case 'paused':
      return { type: 'pf', name: 'warning-triangle-o', classNames: [] };
    default:
      console.error(`Unknown status: ${scanStatus}`);
      return { type: 'pf', name: 'unknown', classNames: [] };
  }
};

const authorizationTypeString = authorizationType => {
  switch (authorizationType) {
    case 'usernamePassword':
      return 'Username & Password';
    case 'sshKey':
      return 'SSH Key';
    default:
      return '';
  }
};

const setStateProp = (prop, data, options) => {
  let { state = {}, initialState = {}, reset = true } = options;
  let obj = { ...state };

  if (!state[prop]) {
    console.error(`Error: Property ${prop} does not exist within the passed state.`, state);
  }

  if (reset && !initialState[prop]) {
    console.warn(`Warning: Property ${prop} does not exist within the passed initialState.`, initialState);
  }

  if (reset) {
    obj[prop] = {
      ...state[prop],
      ...initialState[prop],
      ...data
    };
  } else {
    obj[prop] = {
      ...state[prop],
      ...data
    };
  }

  return obj;
};

const viewPropsChanged = (nextViewOptions, currentViewOptions) => {
  return (
    nextViewOptions.currentPage !== currentViewOptions.currentPage ||
    nextViewOptions.pageSize !== currentViewOptions.pageSize ||
    nextViewOptions.sortField !== currentViewOptions.sortField ||
    nextViewOptions.sortAscending !== currentViewOptions.sortAscending ||
    nextViewOptions.activeFilters !== currentViewOptions.activeFilters
  );
};

const createViewQueryObject = (viewOptions, queryObj) => {
  let queryObject = {
    ...queryObj
  };

  if (viewOptions) {
    if (viewOptions.sortField) {
      queryObject.ordering = viewOptions.sortAscending ? viewOptions.sortField : `-${viewOptions.sortField}`;
    }

    if (viewOptions.activeFilters) {
      viewOptions.activeFilters.forEach(filter => {
        queryObject[filter.field.id] = filter.field.filterType === 'select' ? filter.value.id : filter.value;
      });
    }

    queryObject.page = viewOptions.currentPage;
    queryObject.page_size = viewOptions.pageSize;
  }

  return queryObject;
};

const getErrorMessageFromResults = results => {
  let responseData = _.get(results, 'response.data', results.message);

  if (typeof responseData === 'string') {
    return responseData;
  }

  const getMessages = messageObject => {
    return _.map(messageObject, next => {
      if (_.isString(next)) {
        return next;
      }
      if (_.isArray(next)) {
        return getMessages(next);
      }
    });
  };

  return _.join(getMessages(responseData), '\n');
};

const isIpAddress = name => {
  let vals = name.split('.');
  if (vals.length === 4) {
    return _.find(vals, val => Number.isNaN(val)) === undefined;
  }
  return false;
};

const ipAddressValue = name => {
  const values = name.split('.');
  return values[0] * 0x1000000 + values[1] * 0x10000 + values[2] * 0x100 + values[3] * 1;
};

const DEV_MODE = process.env.REACT_APP_ENV === 'development';

const FULFILLED_ACTION = base => `${base}_FULFILLED`;

const PENDING_ACTION = base => `${base}_PENDING`;

const REJECTED_ACTION = base => `${base}_REJECTED`;

export const helpers = {
  bindMethods,
  devModeNormalizeCount,
  generateId,
  noop,
  sourceTypeString,
  sourceTypeIcon,
  scanTypeString,
  scanStatusString,
  scanTypeIcon,
  scanStatusIcon,
  authorizationTypeString,
  setStateProp,
  viewPropsChanged,
  createViewQueryObject,
  getErrorMessageFromResults,
  isIpAddress,
  ipAddressValue,
  DEV_MODE,
  FULFILLED_ACTION,
  PENDING_ACTION,
  REJECTED_ACTION
};

export default helpers;
