import _ from 'lodash';
import helpers from '../../common/helpers';
import { scansTypes } from '../constants';

const initialState = {
  persist: {},

  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scans: []
  }
};

const scansReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case scansTypes.GET_SCANS_REJECTED:
      return helpers.setStateProp(
        'view',
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
    case scansTypes.GET_SCANS_PENDING:
      return helpers.setStateProp(
        'view',
        {
          pending: true,
          scans: state.view.scans
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.GET_SCANS_FULFILLED:
      return helpers.setStateProp(
        'view',
        {
          scans: action.payload.data.results,
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

export { initialState, scansReducer };

export default scansReducer;
