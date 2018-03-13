import helpers from '../../../common/helpers';
import { sourcesTypes } from '../../constants/index';
import addSourceWizardReducer from '../addSourceWizardReducer';

const initialState = {
  view: {
    show: false,
    add: false,
    edit: false,
    allCredentials: [],
    source: {},
    error: false,
    errorMessage: null,
    stepOneValid: false,
    stepTwoValid: false,
    fulfilled: false
  }
};

describe('AddSourceWizardReducer', function() {
  it('should return the initial state', () => {
    expect(addSourceWizardReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle CREATE_SOURCE_SHOW', () => {
    let dispatched = {
      type: sourcesTypes.CREATE_SOURCE_SHOW
    };

    let resultState = addSourceWizardReducer(undefined, dispatched);

    expect(resultState.view.show).toBeTruthy();
    expect(resultState.view.add).toBeTruthy();
    expect(resultState.view.edit).toBeFalsy();

    dispatched = {
      type: sourcesTypes.UPDATE_SOURCE_HIDE
    };

    resultState = addSourceWizardReducer(resultState, dispatched);

    expect(resultState.view.show).toBeFalsy();
    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle EDIT_SOURCE_SHOW', () => {
    let dispatched = {
      type: sourcesTypes.EDIT_SOURCE_SHOW
    };

    let resultState = addSourceWizardReducer(undefined, dispatched);

    expect(resultState.view.show).toBeTruthy();
    expect(resultState.view.add).toBeFalsy();
    expect(resultState.view.edit).toBeTruthy();

    dispatched = {
      type: sourcesTypes.UPDATE_SOURCE_HIDE
    };

    resultState = addSourceWizardReducer(resultState, dispatched);

    expect(resultState.view.show).toBeFalsy();
    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle ADD_SOURCE_REJECTED', () => {
    let dispatched = {
      type: helpers.rejectedAction(sourcesTypes.ADD_SOURCE),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'ADD ERROR'
          }
        }
      }
    };

    let resultState = addSourceWizardReducer(undefined, dispatched);

    expect(resultState.view.error).toBeTruthy();
    expect(resultState.view.errorMessage).toEqual('ADD ERROR');
  });

  it('should handle UPDATE_SOURCE_REJECTED', () => {
    let dispatched = {
      type: helpers.rejectedAction(sourcesTypes.UPDATE_SOURCE),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'UPDATE ERROR'
          }
        }
      }
    };

    let resultState = addSourceWizardReducer(undefined, dispatched);

    expect(resultState.view.error).toBeTruthy();
    expect(resultState.view.errorMessage).toEqual('UPDATE ERROR');
  });

  it('should handle UPDATE_SOURCE_FULFILLED', () => {
    let dispatched = {
      type: helpers.fulfilledAction(sourcesTypes.UPDATE_SOURCE),
      payload: {
        data: {
          name: 'string',
          source_type: 'network',
          hosts: ['string'],
          port: 0,
          id: 0,
          credentials: [
            {
              id: 0,
              name: 'string',
              cred_type: 'network'
            }
          ],
          options: {
            satellite_version: '5',
            ssl_cert_verify: true,
            ssl_protocol: 'SSLv2',
            disable_ssl: true
          },
          connection: {
            id: 0,
            start_time: '2018-02-21T19:04:18.820Z',
            end_time: '2018-02-21T19:04:18.820Z',
            status: 'created',
            systems_count: 0,
            systems_scanned: 0,
            systems_failed: 0
          }
        }
      }
    };

    let resultState = addSourceWizardReducer(undefined, dispatched);

    expect(Object.keys(resultState.view.source).length).toBeGreaterThan(0);
  });

  it('should handle ADD_SOURCE_FULFILLED', () => {
    let dispatched = {
      type: helpers.fulfilledAction(sourcesTypes.ADD_SOURCE),
      payload: {
        data: {
          name: 'string',
          source_type: 'network',
          hosts: ['string'],
          port: 0,
          id: 0,
          credentials: [
            {
              id: 0,
              name: 'string',
              cred_type: 'network'
            }
          ],
          options: {
            satellite_version: '5',
            ssl_cert_verify: true,
            ssl_protocol: 'SSLv2',
            disable_ssl: true
          },
          connection: {
            id: 0,
            start_time: '2018-02-21T19:04:18.820Z',
            end_time: '2018-02-21T19:04:18.820Z',
            status: 'created',
            systems_count: 0,
            systems_scanned: 0,
            systems_failed: 0
          }
        }
      }
    };

    let resultState = addSourceWizardReducer(undefined, dispatched);

    expect(Object.keys(resultState.view.source).length).toBeGreaterThan(0);
  });
});
