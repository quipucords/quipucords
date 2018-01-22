import * as aboutTypes from './aboutConstants';
import * as credentialsTypes from './credentialsConstants';
import * as factsTypes from './factsConstants';
import * as navigationBarTypes from './navigationBarConstants';
import * as reportsTypes from './reportsConstants';
import * as scansTypes from './scansConstants';
import * as sourcesTypes from './sourcesConstants';
import * as toastNotificationTypes from './toasNotificationConstants';
import * as viewToolbarTypes from './viewToolbarConstants';

const reduxTypes = {
  about: aboutTypes,
  credentials: credentialsTypes,
  facts: factsTypes,
  navigation: navigationBarTypes,
  reports: reportsTypes,
  scans: scansTypes,
  sources: sourcesTypes,
  toastNotifcations: toastNotificationTypes,
  viewToolbar: viewToolbarTypes
};

export {
  reduxTypes,
  aboutTypes,
  credentialsTypes,
  factsTypes,
  navigationBarTypes,
  reportsTypes,
  scansTypes,
  sourcesTypes,
  toastNotificationTypes,
  viewToolbarTypes
};

export default reduxTypes;
