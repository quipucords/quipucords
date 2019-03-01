const authDictionary = {
  sshKey: 'SSH Key',
  usernamePassword: 'Username and Password'
};

const scanStatusDictionary = {
  success: 'Successful',
  completed: 'Completed',
  failed: 'Failed',
  created: 'Created',
  running: 'Running',
  paused: 'Paused',
  pending: 'Pending',
  canceled: 'Canceled'
};

const srcDictionary = {
  network: 'Network',
  satellite: 'Satellite',
  vcenter: 'VCenter'
};

const sslProtocolDictionary = {
  SSLv23: 'SSLv23',
  TLSv1: 'TLSv1',
  TLSv1_1: 'TLSv1.1',
  TLSv1_2: 'TLSv1.2'
};

const dictionary = {
  ...authDictionary,
  ...scanStatusDictionary,
  ...srcDictionary,
  ...sslProtocolDictionary
};

export {
  dictionary as default,
  dictionary,
  authDictionary,
  scanStatusDictionary,
  srcDictionary,
  sslProtocolDictionary
};
