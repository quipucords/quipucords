import _ from 'lodash';
import helpers from '../../common/helpers';
import { scansTypes, sourcesTypes } from '../constants';

const initialState = {
  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    lastRefresh: 0,
    scans: [],
    sourcesCount: 0
  },

  detail: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scan: {}
  },

  connectionResults: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    results: []
  },

  inspectionResults: {
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
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    delete: false
  },

  merge_dialog: {
    show: false,
    scans: [],
    details: false
  }
};

const scansReducer = (state = initialState, action) => {
  switch (action.type) {
    // Error/Rejected
    case helpers.REJECTED_ACTION(scansTypes.GET_SCANS):
      return helpers.setStateProp(
        'view',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload),
          lastRefresh: state.view.lastRefresh
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.GET_SCANS):
      return helpers.setStateProp(
        'view',
        {
          pending: true,
          scans: state.view.scans,
          lastRefresh: state.view.lastRefresh
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.FULFILLED_ACTION(scansTypes.GET_SCANS):
      return helpers.setStateProp(
        'view',
        {
          scans: action.payload.data.results,
          pending: false,
          fulfilled: true,
          lastRefresh: (action.payload.headers && new Date(action.payload.headers.date).getTime()) || 0,
          sourcesCount: state.view.sourcesCount
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.REJECTED_ACTION(scansTypes.GET_SCAN):
      return helpers.setStateProp(
        'detail',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.GET_SCAN):
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
    case helpers.FULFILLED_ACTION(scansTypes.GET_SCAN):
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
    case helpers.REJECTED_ACTION(scansTypes.GET_SCAN_CONNECTION_RESULTS):
      return helpers.setStateProp(
        'connectionResults',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.GET_SCAN_CONNECTION_RESULTS):
      return helpers.setStateProp(
        'connectionResults',
        {
          pending: true,
          results: state.connectionResults.results
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.FULFILLED_ACTION(scansTypes.GET_SCAN_CONNECTION_RESULTS):
      return helpers.setStateProp(
        'connectionResults',
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
    case helpers.REJECTED_ACTION(scansTypes.GET_SCAN_INSPECTION_RESULTS):
      return helpers.setStateProp(
        'inspectionResults',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.GET_SCAN_INSPECTION_RESULTS):
      return helpers.setStateProp(
        'inspectionResults',
        {
          pending: true,
          results: state.inspectionResults.results
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.FULFILLED_ACTION(scansTypes.GET_SCAN_INSPECTION_RESULTS):
      return helpers.setStateProp(
        'inspectionResults',
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
    case helpers.REJECTED_ACTION(scansTypes.GET_SCAN_JOBS):
      return helpers.setStateProp(
        'jobs',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.GET_SCAN_JOBS):
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
    case helpers.FULFILLED_ACTION(scansTypes.GET_SCAN_JOBS):
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
    case helpers.REJECTED_ACTION(scansTypes.ADD_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          add: true,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.ADD_SCAN):
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
    case helpers.FULFILLED_ACTION(scansTypes.ADD_SCAN):
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

    case scansTypes.RESET_SCAN_ADD_STATUS:
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
    case helpers.REJECTED_ACTION(scansTypes.START_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          start: true,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.START_SCAN):
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
    case helpers.FULFILLED_ACTION(scansTypes.START_SCAN):
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
    case helpers.REJECTED_ACTION(scansTypes.CANCEL_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          cancel: true,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.CANCEL_SCAN):
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
    case helpers.FULFILLED_ACTION(scansTypes.CANCEL_SCAN):
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
    case helpers.REJECTED_ACTION(scansTypes.PAUSE_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          pause: true,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.PAUSE_SCAN):
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
    case helpers.FULFILLED_ACTION(scansTypes.PAUSE_SCAN):
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
    case helpers.REJECTED_ACTION(scansTypes.RESTART_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          restart: true,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(scansTypes.RESTART_SCAN):
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
    case helpers.FULFILLED_ACTION(scansTypes.RESTART_SCAN):
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

    case helpers.FULFILLED_ACTION(sourcesTypes.GET_SCANS_SOURCES):
      return helpers.setStateProp(
        'view',
        {
          sourcesCount: _.get(action, 'payload.data.count', 0)
        },
        {
          state,
          reset: false
        }
      );

    // Error/Rejected
    case helpers.REJECTED_ACTION(scansTypes.DELETE_SCAN):
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload),
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.PENDING_ACTION(scansTypes.DELETE_SCAN):
      return helpers.setStateProp(
        'update',
        {
          pending: true,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(scansTypes.DELETE_SCAN):
      return helpers.setStateProp(
        'update',
        {
          fulfilled: true,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case scansTypes.MERGE_SCAN_DIALOG_SHOW:
      return helpers.setStateProp(
        'merge_dialog',
        {
          show: true,
          scans: action.scans,
          details: action.details
        },
        {
          state,
          initialState
        }
      );

    case scansTypes.MERGE_SCAN_DIALOG_HIDE:
      return helpers.setStateProp(
        'merge_dialog',
        {
          show: false
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

scansReducer.initialState = initialState;

export { scansReducer as default, initialState, scansReducer };
