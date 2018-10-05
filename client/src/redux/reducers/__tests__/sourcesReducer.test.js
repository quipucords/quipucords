import helpers from '../../../common/helpers';
import { sourcesTypes } from '../../constants/index';
import sourcesReducer from '../sourcesReducer';

const initialState = {
  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sources: []
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sourceId: '',
    delete: false
  }
};

describe('SourcesReducer', () => {
  it('should return the initial state', () => {
    expect(sourcesReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle DELETE_SOURCE_REJECTED', () => {
    const dispatched = {
      type: helpers.REJECTED_ACTION(sourcesTypes.DELETE_SOURCE),
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

    const resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.update.error).toBeTruthy();
    expect(resultState.update.errorMessage).toEqual('DELETE ERROR');
    expect(resultState.update.delete).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle GET_SOURCES_REJECTED', () => {
    const dispatched = {
      type: helpers.REJECTED_ACTION(sourcesTypes.GET_SOURCES),
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

    const resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.view.error).toBeTruthy();
    expect(resultState.view.errorMessage).toEqual('GET ERROR');

    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle GET_SOURCES_PENDING', () => {
    const dispatched = {
      type: helpers.PENDING_ACTION(sourcesTypes.GET_SOURCES)
    };

    const resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.view.pending).toBeTruthy();

    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle GET_SOURCES_FULFILLED', () => {
    const dispatched = {
      type: helpers.FULFILLED_ACTION(sourcesTypes.GET_SOURCES),
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

    const resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.view.fulfilled).toBeTruthy();
    expect(resultState.view.sources).toHaveLength(4);

    expect(resultState.update).toEqual(initialState.update);
  });
});
