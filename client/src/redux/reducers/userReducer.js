import _ from 'lodash';
import { userTypes } from '../constants';
import helpers from '../../common/helpers';

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

export default function userReducer(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case userTypes.USER_INFO_REJECTED:
      return helpers.setStateProp(
        'user',
        {
          error: action.error,
          errorMessage: _.get(
            action.payload,
            'response.request.responseText',
            action.payload.message
          )
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case userTypes.USER_INFO_PENDING:
      return helpers.setStateProp(
        'user',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case userTypes.USER_INFO_FULFILLED:
      return helpers.setStateProp(
        'user',
        {
          currentUser: action.payload,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case userTypes.USER_AUTH_REJECTED:
      return helpers.setStateProp(
        'session',
        {
          error: action.error,
          errorMessage: _.get(
            action.payload,
            'response.request.responseText',
            action.payload.message
          )
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case userTypes.USER_AUTH_PENDING:
      return helpers.setStateProp(
        'session',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case userTypes.USER_AUTH_FULFILLED:
      return helpers.setStateProp(
        'session',
        {
          loggedIn: true,
          fulfilled: true,
          authToken: action.payload.authToken
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case userTypes.USER_LOGOUT_REJECTED:
      return helpers.setStateProp(
        'session',
        {
          error: action.error,
          errorMessage: _.get(
            action.payload,
            'response.request.responseText',
            action.payload.message
          )
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case userTypes.USER_LOGOUT_PENDING:
      return helpers.setStateProp(
        'session',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case userTypes.USER_LOGOUT_FULFILLED:
      return helpers.setStateProp(
        'session',
        {
          loggedIn: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    default:
      return state;
  }
}
