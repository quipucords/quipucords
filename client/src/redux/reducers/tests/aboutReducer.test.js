import aboutReducer from '../aboutReducer';

describe('AboutReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      show: false
    };

    expect(aboutReducer(undefined, {})).toEqual(initialState);
  });
});
