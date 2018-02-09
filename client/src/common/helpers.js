export const bindMethods = (context, methods) => {
  methods.forEach(method => {
    context[method] = context[method].bind(context);
  });
};

export const noop = Function.prototype;

export const sourceTypeString = sourceType => {
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

export const sourceTypeIcon = sourceType => {
  switch (sourceType) {
    case 'vcenter':
      return { type: 'pf', name: 'virtual-machine' };
    case 'network':
      return { type: 'pf', name: 'network' };
    case 'satellite':
      return { type: 'fa', name: 'space-shuttle' };
    default:
      return { type: '', name: '' };
  }
};

export const scanTypeString = scanType => {
  switch (scanType) {
    case 'connect':
      return 'Connection Scan';
    case 'inspect':
      return 'Inspection Scan';
    default:
      return '';
  }
};

export const scanTypeIcon = scanType => {
  switch (scanType) {
    case 'connect':
      return { type: 'pf', name: 'connected' };
    case 'inspect':
      return { type: 'fa', name: 'search' };
    default:
      return { type: '', name: '' };
  }
};

export const scanStatusString = scanStatus => {
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

export const authorizationTypeString = authorizationType => {
  switch (authorizationType) {
    case 'usernamePassword':
      return 'Username & Password';
    case 'sshKey':
      return 'SSH Key';
    default:
      return '';
  }
};

export const setStateProp = (prop, data, options) => {
  let { state = {}, initialState = {}, reset = true } = options;
  let obj = { ...state };

  if (!state[prop]) {
    console.error(
      `Error: Property ${prop} does not exist within the passed state.`,
      state
    );
  }

  if (reset && !initialState[prop]) {
    console.warn(
      `Warning: Property ${prop} does not exist within the passed initialState.`,
      initialState
    );
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

export const viewPropsChanged = (nextViewOptions, currentViewOptions) => {
  return (
    nextViewOptions.currentPage !== currentViewOptions.currentPage ||
    nextViewOptions.pageSize !== currentViewOptions.pageSize ||
    nextViewOptions.sortField !== currentViewOptions.sortField ||
    nextViewOptions.sortAscending !== currentViewOptions.sortAscending ||
    nextViewOptions.activeFilters !== currentViewOptions.activeFilters
  );
};

export const viewQueryObject = (viewOptions, queryObj) => {

  let queryObject = {
    ...queryObj
  };

  if (viewOptions) {
    if (viewOptions.sortField) {
      queryObject.ordering = viewOptions.sortAscending
        ? viewOptions.sortField
        : `-${viewOptions.sortField}`;
    }

    if (viewOptions.activeFilters) {
      viewOptions.activeFilters.forEach(filter => {
        queryObject[filter.id] =
          filter.filterType === 'select'
            ? filter.filterValue.id
            : filter.filterValue;
      });
    }

    queryObject.page = viewOptions.currentPage;
    queryObject.page_size = viewOptions.pageSize;
  }

  return queryObject;
};

export const helpers = {
  bindMethods: bindMethods,
  noop: noop,
  sourceTypeString: sourceTypeString,
  sourceTypeIcon: sourceTypeIcon,
  scanTypeString: scanTypeString,
  scanStatusString: scanStatusString,
  scanTypeIcon: scanTypeIcon,
  authorizationTypeString: authorizationTypeString,
  setStateProp: setStateProp,
  viewPropsChanged: viewPropsChanged,
  viewQueryObject: viewQueryObject
};

export default helpers;
