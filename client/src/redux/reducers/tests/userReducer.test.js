import { userTypes } from '../../constants/index';
import userReducer from '../userReducer';
import helpers from "../../../common/helpers";

const initialState = {
  session: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    loggedIn: false,
    authToken: null
  },
  user: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    currentUser: {}
  }
};

describe('userReducer', function() {
  it('should return the initial state', () => {
    expect(userReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle USER_INFO_REJECTED', () => {
    let dispatched = {
      type: userTypes.USER_INFO_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'USER INFO ERROR'
          }
        }
      }
    };

    let resultState = userReducer(undefined, dispatched);
    expect(resultState.user.error).toBeTruthy();
    expect(resultState.user.errorMessage).toEqual('USER INFO ERROR');

    expect(resultState.session).toEqual(initialState.session);
  });

  it('should handle USER_INFO_PENDING', () => {
    let dispatched = {
      type: userTypes.USER_INFO_PENDING
    };

    let resultState = userReducer(undefined, dispatched);

    expect(resultState.user.pending).toBeTruthy();
    expect(resultState.session).toEqual(initialState.session);
  });

  it('should handle USER_INFO_FULFILLED', () => {
    let dispatched = {
      type: userTypes.USER_INFO_FULFILLED,
      payload: {
        data: {
          userName: 'admin',
          id: 1
        }
      }
    };

    let resultState = userReducer(undefined, dispatched);

    expect(resultState.user.fulfilled).toBeTruthy();
    expect(resultState.user.currentUser.userName).toEqual('admin');

    expect(resultState.session).toEqual(initialState.session);
  });

  it('should handle USER_AUTH_REJECTED', () => {
    let dispatched = {
      type: userTypes.USER_AUTH_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'USER AUTH ERROR'
          }
        }
      }
    };

    let resultState = userReducer(undefined, dispatched);
    expect(resultState.session.error).toBeTruthy();
    expect(resultState.session.errorMessage).toEqual('USER AUTH ERROR');

    expect(resultState.user).toEqual(initialState.user);
  });

  it('should handle USER_AUTH_PENDING', () => {
    let dispatched = {
      type: userTypes.USER_AUTH_PENDING
    };

    let resultState = userReducer(undefined, dispatched);

    expect(resultState.session.pending).toBeTruthy();
    expect(resultState.user).toEqual(initialState.user);
  });

  it('should handle USER_AUTH_FULFILLED', () => {
    let dispatched = {
      type: userTypes.USER_AUTH_FULFILLED,
      payload: {
        authToken: 'spoof'
      }
    };

    let resultState = userReducer(undefined, dispatched);

    expect(resultState.session.fulfilled).toBeTruthy();
    expect(resultState.session.loggedIn).toBeTruthy();
    expect(resultState.session.wasLoggedIn).toBeTruthy();
    expect(resultState.session.authToken).toBeTruthy();
    expect(resultState.session.authToken).toEqual('spoof');

    expect(resultState.user).toEqual(initialState.user);
  });

  it('should handle USER_LOGOUT_REJECTED', () => {
    let dispatched = {
      type: userTypes.USER_LOGOUT_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'USER LOGOUT ERROR'
          }
        }
      }
    };

    let resultState = userReducer(undefined, dispatched);
    expect(resultState.session.error).toBeTruthy();
    expect(resultState.session.errorMessage).toEqual('USER LOGOUT ERROR');

    expect(resultState.user).toEqual(initialState.user);
  });

  it('should handle USER_LOGOUT_PENDING', () => {
    let dispatched = {
      type: userTypes.USER_LOGOUT_PENDING
    };

    let resultState = userReducer(undefined, dispatched);

    expect(resultState.session.pending).toBeTruthy();
    expect(resultState.user).toEqual(initialState.user);
  });

  it('should handle USER_LOGOUT_FULFILLED', () => {
    let dispatched = {
      type: userTypes.USER_AUTH_FULFILLED,
      payload: {
        authToken: 'spoof'
      }
    };

    let resultState = userReducer(undefined, dispatched);

    expect(resultState.session.fulfilled).toBeTruthy();
    expect(resultState.session.loggedIn).toBeTruthy();
    expect(resultState.session.wasLoggedIn).toBeTruthy();
    expect(resultState.session.authToken).toBeTruthy();
    expect(resultState.session.authToken).toEqual('spoof');

    dispatched = {
      type: userTypes.USER_LOGOUT_FULFILLED
    };

    resultState = userReducer(resultState, dispatched);

    expect(resultState.session.fulfilled).toBeTruthy();
    expect(resultState.session.loggedIn).toBeFalsy();
    expect(resultState.session.wasLoggedIn).toBeTruthy();

    expect(resultState.user).toEqual(initialState.user);
  });
});
