import _ from 'lodash';

const bindMethods = (context, methods) => {
  methods.forEach(method => {
    context[method] = context[method].bind(context);
  });
};

const noop = Function.prototype;

const generateId = prefix => `${prefix || 'generatedid'}-${Math.ceil(1e5 * Math.random())}`;

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
      return '';
  }
};

const scanStatusIcon = scanStatus => {
  switch (scanStatus) {
    case 'completed':
      return { type: 'pf', name: 'ok' };
    case 'failed':
    case 'canceled':
      return { type: 'pf', name: 'error-circle-o' };
    case 'created':
    case 'pending':
    case 'running':
      return { type: 'fa', name: 'spinner' };
    case 'paused':
      return { type: 'pf', name: 'warning-triangle-o' };
    default:
      return null;
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
  let message = '';

  if (responseData instanceof String) {
    return responseData;
  }

  if (responseData.forEach !== undefined) {
    _.forEach(responseData, errCase => {
      if (message !== '') {
        message += '\n';
      }
      message += `Error: ${errCase}`;
    });
    return message;
  }

  const keys = _.keys(responseData);
  const hasDetails = keys.find(key => {
    return key === 'non_field_errors' || key === 'detail' || key === 'options';
  });

  _.forEach(keys, key => {
    let errorContext = 'Error';
    if (key !== 'non_field_errors' && key !== 'detail' && key !== 'options') {
      errorContext = key;
    }
    if (responseData[key] instanceof String) {
      if (message !== '') {
        message += '\n';
      }
      message += `${errorContext}: ${responseData[key]}`;
    } else if (responseData[key].forEach !== undefined) {
      if (errorContext !== key || !hasDetails) {
        _.forEach(responseData[key], errCase => {
          if (message !== '') {
            message += '\n';
          }
          message += `${errorContext}: ${errCase}`;
        });
      }
    } else {
      if (message !== '') {
        message += '\n';
      }
      message += `${errorContext}: ${responseData[key]}`;
    }
  });

  return message || results.message;
};

const DEV_MODE = process.env.REACT_APP_ENV === 'development';
const normalizeCount = (count, modulus = 100) => {
  return Math.abs(count) % modulus;
};

export const helpers = {
  bindMethods,
  noop,
  generateId,
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
  DEV_MODE,
  normalizeCount
};

export default helpers;
