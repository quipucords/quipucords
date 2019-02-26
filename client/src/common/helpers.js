import moment from 'moment';
import _get from 'lodash/get';
import _set from 'lodash/set';

const devModeNormalizeCount = (count, modulus = 100) => Math.abs(count) % modulus;

const downloadData = (data = '', fileName = 'download.txt', fileType = 'text/plain') =>
  new Promise((resolve, reject) => {
    try {
      const blob = new Blob([data], { type: fileType });

      if (window.navigator && window.navigator.msSaveBlob) {
        window.navigator.msSaveBlob(blob, fileName);
        resolve({ fileName, data });
      } else {
        const anchorTag = window.document.createElement('a');

        anchorTag.href = window.URL.createObjectURL(blob);
        anchorTag.style.display = 'none';
        anchorTag.download = fileName;

        window.document.body.appendChild(anchorTag);

        anchorTag.click();

        setTimeout(() => {
          window.document.body.removeChild(anchorTag);
          window.URL.revokeObjectURL(blob);
          resolve({ fileName, data });
        }, 250);
      }
    } catch (error) {
      reject(error);
    }
  });

const generateId = prefix =>
  `${prefix || 'generatedid'}-${(process.env.REACT_APP_ENV !== 'test' && Math.ceil(1e5 * Math.random())) || ''}`;

const noop = Function.prototype;

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

const setPropIfDefined = (obj, props, value) => (obj && value !== undefined ? _set(obj, props, value) : obj);

const setPropIfTruthy = (obj, props, value) => (obj && value ? _set(obj, props, value) : obj);

const setStateProp = (prop, data, options) => {
  const { state = {}, initialState = {}, reset = true } = options;
  let obj = { ...state };

  if (prop && !state[prop]) {
    console.error(`Error: Property ${prop} does not exist within the passed state.`, state);
  }

  if (reset && prop && !initialState[prop]) {
    console.warn(`Warning: Property ${prop} does not exist within the passed initialState.`, initialState);
  }

  if (reset && prop) {
    obj[prop] = {
      ...state[prop],
      ...initialState[prop],
      ...data
    };
  } else if (reset && !prop) {
    obj = {
      ...state,
      ...initialState,
      ...data
    };
  } else if (prop) {
    obj[prop] = {
      ...state[prop],
      ...data
    };
  } else {
    obj = {
      ...state,
      ...data
    };
  }

  return obj;
};

const viewPropsChanged = (nextViewOptions, currentViewOptions) =>
  nextViewOptions.currentPage !== currentViewOptions.currentPage ||
  nextViewOptions.pageSize !== currentViewOptions.pageSize ||
  nextViewOptions.sortField !== currentViewOptions.sortField ||
  nextViewOptions.sortAscending !== currentViewOptions.sortAscending ||
  nextViewOptions.activeFilters !== currentViewOptions.activeFilters;

const createViewQueryObject = (viewOptions, queryObj) => {
  const queryObject = {
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

const getMessageFromResults = (results, filter = null) => {
  const status = _get(results, 'response.status', results.status);
  const statusResponse = _get(results, 'response.statusText', results.statusText);
  const messageResponse = _get(results, 'response.data', results.message);
  const detailResponse = _get(results, 'response.data', results.detail);

  const messages = {
    status: status || 0,
    messages: {},
    message: null
  };

  const displayStatus = status >= 500 ? `${status} ` : '';

  if (!messageResponse && !detailResponse) {
    if (status < 400) {
      messages.message = statusResponse;
      return messages;
    }

    if (status >= 500 || status === undefined) {
      messages.message = `${status || ''} Server is currently unable to handle this request.`;
      return messages;
    }
  }

  if (status >= 500 && /Request\sURL:/.test(messageResponse)) {
    messages.message = `${status} ${messageResponse.split(/Request\sURL:/)[0]}`;
    return messages;
  }

  if (typeof messageResponse === 'string') {
    messages.message = `${displayStatus}${messageResponse}`;
    return messages;
  }

  if (typeof detailResponse === 'string') {
    messages.message = `${displayStatus}${detailResponse}`;
    return messages;
  }

  const getMessages = (messageObjectArrayString, filterField) => {
    const parsed = {};
    const parsedFiltered = {};
    const filterFields = (Array.isArray(filterField) && filterField) || (filterField && [filterField]) || [];

    if (messageObjectArrayString && typeof messageObjectArrayString === 'string') {
      return messageObjectArrayString.replace(/\[object\sObject\]/g, '');
    }

    if (Array.isArray(messageObjectArrayString)) {
      return getMessages(messageObjectArrayString.join('\n'));
    }

    Object.keys(messageObjectArrayString).forEach(key => {
      const message = getMessages(messageObjectArrayString[key]);

      if (filterFields.length && filterFields.includes(key)) {
        parsedFiltered[key] = message;
      }

      parsed[key] = message;
    });

    return filterFields.length ? parsedFiltered : parsed;
  };

  messages.messages = getMessages(messageResponse || detailResponse, filter);
  messages.message = `${displayStatus}${Object.values(messages.messages).join('\n')}`;

  return messages;
};

const getStatusFromResults = results => {
  let status = _get(results, 'response.status', results.status);

  if (status === undefined) {
    status = 0;
  }

  return status;
};

const getTimeStampFromResults = results => moment(_get(results, 'headers.date', Date.now())).format('YYYYMMDD_HHmmss');

const isIpAddress = name => {
  const vals = name.split('.');
  if (vals.length === 4) {
    return vals.find(val => Number.isNaN(val)) === undefined;
  }
  return false;
};

const ipAddressValue = name => {
  const values = name.split('.');
  return values[0] * 0x1000000 + values[1] * 0x10000 + values[2] * 0x100 + values[3] * 1;
};

const DEV_MODE = process.env.REACT_APP_ENV === 'development';

const TEST_MODE = process.env.REACT_APP_ENV === 'test';

const RH_BRAND = process.env.REACT_APP_RH_BRAND === 'true';

const FULFILLED_ACTION = base => `${base}_FULFILLED`;

const PENDING_ACTION = base => `${base}_PENDING`;

const REJECTED_ACTION = base => `${base}_REJECTED`;

const helpers = {
  devModeNormalizeCount,
  downloadData,
  generateId,
  noop,
  sourceTypeIcon,
  scanTypeIcon,
  scanStatusIcon,
  setPropIfDefined,
  setPropIfTruthy,
  setStateProp,
  viewPropsChanged,
  createViewQueryObject,
  getMessageFromResults,
  getStatusFromResults,
  getTimeStampFromResults,
  isIpAddress,
  ipAddressValue,
  DEV_MODE,
  TEST_MODE,
  RH_BRAND,
  FULFILLED_ACTION,
  PENDING_ACTION,
  REJECTED_ACTION
};

export { helpers as default, helpers };
