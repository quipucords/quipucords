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

const dictionary = {
  ...authDictionary,
  ...scanStatusDictionary,
  ...srcDictionary
};

export { dictionary as default, dictionary, authDictionary, scanStatusDictionary, srcDictionary };
