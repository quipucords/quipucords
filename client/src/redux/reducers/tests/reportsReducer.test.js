import { reportsTypes } from '../../constants/index';
import reportsReducer from '../reportsReducer';

const initialState = {
  persist: {},

  deployments: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    reports: []
  },

  details: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    reports: []
  }
};

describe('ReportsReducer', function() {
  it('should return the initial state', () => {
    expect(reportsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_REPORT_DEPLOYMENTS_REJECTED', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORT_DEPLOYMENTS_REJECTED,
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

    let resultState = reportsReducer(undefined, dispatched);
    expect(resultState.deployments.error).toBeTruthy();
    expect(resultState.deployments.errorMessage).toEqual('GET ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle GET_REPORT_DETAILS_REJECTED', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORT_DETAILS_REJECTED,
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

    let resultState = reportsReducer(undefined, dispatched);
    expect(resultState.details.error).toBeTruthy();
    expect(resultState.details.errorMessage).toEqual('GET ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle GET_REPORT_DEPLOYMENTS_PENDING', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORT_DEPLOYMENTS_PENDING
    };

    let resultState = reportsReducer(undefined, dispatched);

    expect(resultState.deployments.pending).toBeTruthy();
    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle GET_REPORT_DETAILS_PENDING', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORT_DETAILS_PENDING
    };

    let resultState = reportsReducer(undefined, dispatched);

    expect(resultState.details.pending).toBeTruthy();
    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle GET_REPORT_DEPLOYMENTS_FULFILLED', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORT_DEPLOYMENTS_FULFILLED,
      payload: {
        data: [
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
    };

    let resultState = reportsReducer(undefined, dispatched);

    expect(resultState.deployments.fulfilled).toBeTruthy();
    expect(resultState.deployments.reports).toHaveLength(4);

    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle GET_REPORT_DETAILS_FULFILLED', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORT_DETAILS_FULFILLED,
      payload: {
        data: [
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
    };

    let resultState = reportsReducer(undefined, dispatched);

    expect(resultState.details.fulfilled).toBeTruthy();
    expect(resultState.details.reports).toHaveLength(4);

    expect(resultState.persist).toEqual(initialState.persist);
  });
});
