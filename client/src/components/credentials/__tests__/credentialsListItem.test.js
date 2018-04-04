import React from 'react';
import configureMockStore from 'redux-mock-store';
import CredentialListItem from '../credentialListItem';
import { mount } from 'enzyme';
import { viewTypes } from '../../../redux/constants/';

describe('CredentialListItem Component', function() {
  const generateEmptyStore = () =>
    configureMockStore()({ credentials: {}, viewOptions: { [viewTypes.CREDENTIALS_VIEW]: {} } });

  it('should render a basic component with a credential type', () => {
    const store = generateEmptyStore();
    const props = {
      item: {
        id: 1,
        cred_type: 'network'
      }
    };

    const component = mount(<CredentialListItem {...props} />, { context: { store } });

    expect(component.render()).toMatchSnapshot();
  });
});
