import React from 'react';
import configureMockStore from 'redux-mock-store';
import SourceListItem from '../sourceListItem';
import { mount } from 'enzyme';
import { viewTypes } from '../../../redux/constants/';

describe('SourceListItem Component', function() {
  const generateEmptyStore = () => configureMockStore()({ sources: {}, viewOptions: { [viewTypes.SOURCES_VIEW]: {} } });

  it('should render a basic component', () => {
    const store = generateEmptyStore();
    const props = {
      item: {
        id: 1,
        source_type: 'network'
      }
    };

    const component = mount(<SourceListItem {...props} />, { context: { store } });

    expect(component.render()).toMatchSnapshot();
  });
});
