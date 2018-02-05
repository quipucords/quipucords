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

export const helpers = {
  bindMethods: bindMethods,
  noop: noop,
  sourceTypeString: sourceTypeString,
  sourceTypeIcon: sourceTypeIcon,
  scanTypeString: scanTypeString,
  scanTypeIcon: scanTypeIcon,
  authorizationTypeString: authorizationTypeString
};
