import _ from 'lodash';
import helpers from '../../common/helpers';
import { scansTypes } from '../constants';

const initialState = {
  persist: {
    expandedScans: []
  },

  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scans: []
  },

  detail: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scan: {}
  },

  results: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    results: []
  },

  jobs: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    jobs: []
  },

  action: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    add: false,
    start: false,
    cancel: false,
    pause: false,
    restart: false
  }
};

const expandedIndex = function(state, scan) {
  return _.findIndex(state.persist.expandedScans, nextSelected => {
    return nextSelected.id === _.get(scan, 'id');
  });
};

const scansReducer = function(state = initialState, action) {
  switch (action.type) {
    // Persist
    case scansTypes.EXPAND_SCAN:
      const expandIndex = expandedIndex(state, action.scan);
      let newExpansions;

      if (expandIndex === -1) {
        newExpansions = [...state.persist.expandedScans];
      } else {
        newExpansions = [
          ...state.persist.expandedScans.slice(0, expandIndex),
          ...state.persist.expandedScans.slice(expandIndex + 1)
        ];
      }

      if (action.expandType) {
        newExpansions.push({
          id: action.scan.id,
          expandType: action.expandType
        });
      }

      return helpers.setStateProp(
        'persist',
        {
          expandedScans: newExpansions
        },
        {
          state,
          reset: false
        }
      );

    // Error/Rejected
    case scansTypes.GET_SCANS_REJECTED:
      return helpers.setStateProp(
        'view',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
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
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.GET_SCAN_REJECTED:
      return helpers.setStateProp(
        'detail',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.GET_SCAN_PENDING:
      return helpers.setStateProp(
        'detail',
        {
          pending: true,
          scan: state.detail.scans
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.GET_SCAN_FULFILLED:
      return helpers.setStateProp(
        'detail',
        {
          scan: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.GET_SCAN_RESULTS_REJECTED:
      return helpers.setStateProp(
        'results',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.GET_SCAN_RESULTS_PENDING:
      return helpers.setStateProp(
        'results',
        {
          pending: true,
          results: state.results.results
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.GET_SCAN_RESULTS_FULFILLED:
      return helpers.setStateProp(
        'results',
        {
          results: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.GET_SCAN_JOBS_REJECTED:
      return helpers.setStateProp(
        'jobs',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.GET_SCAN_JOBS_PENDING:
      return helpers.setStateProp(
        'jobs',
        {
          pending: true,
          jobs: state.jobs.jobs
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.GET_SCAN_JOBS_FULFILLED:
      return helpers.setStateProp(
        'jobs',
        {
          jobs: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.ADD_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          add: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.ADD_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          add: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.ADD_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          add: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case scansTypes.ADD_SCAN_RESET_STATUS:
      return helpers.setStateProp(
        'action',
        {
          error: false,
          errorMessage: '',
          fulfilled: false
        },
        {
          state,
          reset: false
        }
      );

    // Error/Rejected
    case scansTypes.START_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          start: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.START_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          start: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.START_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          start: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.CANCEL_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          cancel: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.CANCEL_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          cancel: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.CANCEL_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          cancel: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.PAUSE_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          pause: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.PAUSE_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          pause: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.PAUSE_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          pause: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case scansTypes.RESTART_SCAN_REJECTED:
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          restart: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.RESTART_SCAN_PENDING:
      return helpers.setStateProp(
        'action',
        {
          restart: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.RESTART_SCAN_FULFILLED:
      return helpers.setStateProp(
        'action',
        {
          restart: true,
          pending: false,
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
