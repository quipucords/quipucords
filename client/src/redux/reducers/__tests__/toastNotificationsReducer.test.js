import toastNotificationsReducer from '../toastNotificationsReducer';

describe('toastNotificationsReducer', () => {
  it('should return the initial state', () => {
    const initialState = {
      toasts: [],
      paused: false
    };

    expect(toastNotificationsReducer(undefined, {})).toEqual(initialState);
  });
});
