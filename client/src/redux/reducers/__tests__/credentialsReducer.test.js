import helpers from '../../../common/helpers';
import { credentialsTypes } from '../../constants/index';
import credentialsReducer from '../credentialsReducer';

const initialState = {
  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    credentials: []
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    credential: null,
    credentialType: '',
    show: false,
    add: false,
    edit: false,
    delete: false
  }
};

describe('CredentialsReducer', () => {
  it('should return the initial state', () => {
    expect(credentialsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle CREATE_CREDENTIAL_SHOW', () => {
    let dispatched = {
      type: credentialsTypes.CREATE_CREDENTIAL_SHOW
    };

    let resultState = credentialsReducer(undefined, dispatched);

    expect(resultState.update.show).toBeTruthy();
    expect(resultState.update.add).toBeTruthy();
    expect(resultState.update.edit).toBeFalsy();
    expect(resultState.update.delete).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);

    dispatched = {
      type: credentialsTypes.UPDATE_CREDENTIAL_HIDE
    };
    resultState = credentialsReducer(resultState, dispatched);

    expect(resultState.update.show).toBeFalsy();
    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle EDIT_CREDENTIAL_SHOW', () => {
    let dispatched = {
      type: credentialsTypes.EDIT_CREDENTIAL_SHOW
    };

    let resultState = credentialsReducer(undefined, dispatched);

    expect(resultState.update.show).toBeTruthy();
    expect(resultState.update.add).toBeFalsy();
    expect(resultState.update.edit).toBeTruthy();
    expect(resultState.update.delete).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);

    dispatched = {
      type: credentialsTypes.UPDATE_CREDENTIAL_HIDE
    };
    resultState = credentialsReducer(resultState, dispatched);

    expect(resultState.update.show).toBeFalsy();
    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle ADD_CREDENTIAL_REJECTED', () => {
    const dispatched = {
      type: helpers.REJECTED_ACTION(credentialsTypes.ADD_CREDENTIAL),
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

    const resultState = credentialsReducer(undefined, dispatched);

    expect(resultState.update.error).toBeTruthy();
    expect(resultState.update.errorMessage).toEqual('ADD ERROR');
    expect(resultState.update.add).toBeTruthy();
    expect(resultState.update.pending).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle DELETE_CREDENTIAL_REJECTED', () => {
    const dispatched = {
      type: helpers.REJECTED_ACTION(credentialsTypes.DELETE_CREDENTIAL),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'DELETE ERROR'
          }
        }
      }
    };

    const resultState = credentialsReducer(undefined, dispatched);

    expect(resultState.update.error).toBeTruthy();
    expect(resultState.update.errorMessage).toEqual('DELETE ERROR');
    expect(resultState.update.delete).toBeTruthy();
    expect(resultState.update.pending).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle UPDATE_CREDENTIAL_REJECTED', () => {
    const dispatched = {
      type: helpers.REJECTED_ACTION(credentialsTypes.UPDATE_CREDENTIAL),
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

    const resultState = credentialsReducer(undefined, dispatched);

    expect(resultState.update.error).toBeTruthy();
    expect(resultState.update.errorMessage).toEqual('UPDATE ERROR');
    expect(resultState.update.edit).toBeTruthy();
    expect(resultState.update.pending).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle GET_CREDENTIALS_REJECTED', () => {
    const dispatched = {
      type: helpers.REJECTED_ACTION(credentialsTypes.GET_CREDENTIALS),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET ERROR'
          }
        }
      }
    };

    const resultState = credentialsReducer(undefined, dispatched);

    expect(resultState.view.error).toBeTruthy();
    expect(resultState.view.errorMessage).toEqual('GET ERROR');

    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle GET_CREDENTIALS_PENDING', () => {
    const dispatched = {
      type: helpers.PENDING_ACTION(credentialsTypes.GET_CREDENTIALS)
    };

    const resultState = credentialsReducer(undefined, dispatched);

    expect(resultState.view.pending).toBeTruthy();

    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle GET_CREDENTIALS_FULFILLED', () => {
    const dispatched = {
      type: helpers.FULFILLED_ACTION(credentialsTypes.GET_CREDENTIALS),
      payload: {
        data: {
          results: [
            {
              name: '1',
              id: 1
            },
            {
              name: '2',
              id: 2
            },
            {
              name: '3',
              id: 3
            },
            {
              name: '4',
              id: 4
            }
          ]
        }
      }
    };

    const resultState = credentialsReducer(undefined, dispatched);

    expect(resultState.view.fulfilled).toBeTruthy();
    expect(resultState.view.credentials).toHaveLength(4);

    expect(resultState.update).toEqual(initialState.update);
  });
});
