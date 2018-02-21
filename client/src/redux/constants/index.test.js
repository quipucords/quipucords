import reduxTypes from './';
import * as aboutTypes from './aboutConstants';
import * as confirmationModalTypes from './confirmationModalConstants';
import * as credentialsTypes from './credentialsConstants';
import * as factsTypes from './factsConstants';
import * as navigationBarTypes from './navigationBarConstants';
import * as reportsTypes from './reportsConstants';
import * as scansTypes from './scansConstants';
import * as sourcesTypes from './sourcesConstants';
import * as toastNotificationTypes from './toasNotificationConstants';
import * as userTypes from './userConstants';
import * as viewTypes from './viewConstants';
import * as viewPaginationTypes from './viewPaginationConstants';
import * as viewToolbarTypes from './viewToolbarConstants';

describe('reduxTypes', function() {
  it('should export the same number of name-spaced types as imported', () => {
    expect(Object.keys(reduxTypes)).toHaveLength(13);
  });

  it('should return types that are defined', () => {
    Object.keys(reduxTypes).forEach(type => expect(reduxTypes[type]).toBeDefined());
  });

  it('should return types that match', () => {
    expect(reduxTypes.about).toEqual(aboutTypes);
    expect(reduxTypes.confirmationModal).toEqual(confirmationModalTypes);
    expect(reduxTypes.credentials).toEqual(credentialsTypes);
    expect(reduxTypes.facts).toEqual(factsTypes);
    expect(reduxTypes.navigation).toEqual(navigationBarTypes);
    expect(reduxTypes.reports).toEqual(reportsTypes);
    expect(reduxTypes.scans).toEqual(scansTypes);
    expect(reduxTypes.sources).toEqual(sourcesTypes);
    expect(reduxTypes.toastNotifications).toEqual(toastNotificationTypes);
    expect(reduxTypes.user).toEqual(userTypes);
    expect(reduxTypes.view).toEqual(viewTypes);
    expect(reduxTypes.viewPagination).toEqual(viewPaginationTypes);
    expect(reduxTypes.viewToolbar).toEqual(viewToolbarTypes);
  });
});
