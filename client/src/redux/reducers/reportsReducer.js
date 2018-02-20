import _ from 'lodash';
import helpers from '../../common/helpers';
import { reportsTypes } from '../constants';

const initialState = {
  persist: {},

  search: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    reports: []
  }
};

const reportsReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case reportsTypes.GET_REPORTS_REJECTED:
      return helpers.setStateProp(
        'search',
        {
          error: action.error,
          errorMessage: _.get(action.payload, 'response.request.responseText', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case reportsTypes.GET_REPORTS_PENDING:
      return helpers.setStateProp(
        'search',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case reportsTypes.GET_REPORTS_FULFILLED:
      return helpers.setStateProp(
        'search',
        {
          reports: action.payload.data,
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
};

export { initialState, reportsReducer };

export default reportsReducer;
