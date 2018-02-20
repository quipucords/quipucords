import { scansTypes } from '../../constants/index';
import scansReducer from '../scansReducer';

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

describe('scansReducer', function() {
  it('should return the initial state', () => {
    expect(scansReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_SCANS_REJECTED', () => {
    let dispatched = {
      type: scansTypes.GET_SCANS_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'GET ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.error).toBeTruthy();
    expect(resultState.view.errorMessage).toEqual('GET ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle GET_SCANS_PENDING', () => {
    let dispatched = {
      type: scansTypes.GET_SCANS_PENDING
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.pending).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle GET_SCANS_FULFILLED', () => {
    let dispatched = {
      type: scansTypes.GET_SCANS_FULFILLED,
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

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.fulfilled).toBeTruthy();
    expect(resultState.view.scans).toHaveLength(4);

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.update).toEqual(initialState.update);
  });
});
