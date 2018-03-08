import * as credentialsTypes from './credentialsConstants';
import * as factsTypes from './factsConstants';
import * as reportsTypes from './reportsConstants';
import * as scansTypes from './scansConstants';
import * as sourcesTypes from './sourcesConstants';
import * as toastNotificationTypes from './toasNotificationConstants';
import * as viewTypes from './viewConstants';
import * as viewPaginationTypes from './viewPaginationConstants';
import * as viewToolbarTypes from './viewToolbarConstants';
import * as confirmationModalTypes from './confirmationModalConstants';
import * as userTypes from './userConstants';
import * as statusTypes from './statusConstants';

const reduxTypes = {
  credentials: credentialsTypes,
  facts: factsTypes,
  reports: reportsTypes,
  scans: scansTypes,
  sources: sourcesTypes,
  toastNotifications: toastNotificationTypes,
  view: viewTypes,
  viewPagination: viewPaginationTypes,
  viewToolbar: viewToolbarTypes,
  confirmationModal: confirmationModalTypes,
  user: userTypes,
  status: statusTypes
};

export {
  reduxTypes,
  credentialsTypes,
  factsTypes,
  reportsTypes,
  scansTypes,
  sourcesTypes,
  toastNotificationTypes,
  viewTypes,
  viewPaginationTypes,
  viewToolbarTypes,
  confirmationModalTypes,
  userTypes,
  statusTypes
};

export default reduxTypes;
