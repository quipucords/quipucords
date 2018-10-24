import * as credentialsActions from './credentialsActions';
import * as factsActions from './factsActions';
import * as reportsActions from './reportsActions';
import * as scansActions from './scansActions';
import * as sourcesActions from './sourcesActions';
import * as statusActions from './statusActions';
import * as userActions from './userActions';

const actions = {
  credentials: credentialsActions,
  facts: factsActions,
  reports: reportsActions,
  scans: scansActions,
  sources: sourcesActions,
  status: statusActions,
  user: userActions
};

const reduxActions = { ...actions };

export {
  reduxActions as default,
  reduxActions,
  actions,
  credentialsActions,
  factsActions,
  reportsActions,
  scansActions,
  sourcesActions,
  statusActions,
  userActions
};
