import React from 'react';
import PropTypes from 'prop-types';
import { Dropdown } from 'patternfly-react';
import helpers from '../../common/helpers';
import _ from 'lodash';

class DropdownSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = { dropdownIsOpen: false };
  }

  render() {
    const { dropdownIsOpen } = this.state;
    const { id, title, multiselect, children } = this.props;
    const filteredProps = _.omit(this.props, ['multiselect']);

    const toggleDropDown = (a, b, c) => {
      this.setState({
        dropdownIsOpen: (c && c.source === 'select') || !dropdownIsOpen
      });
    };

    const passOnClick = callback => {
      return function() {
        if (callback) {
          callback.apply(this, arguments);
        }

        toggleDropDown.apply(this, arguments);
      };
    };

    if (!multiselect) {
      return (
        <Dropdown id={id || helpers.generateId()} {...filteredProps}>
          <Dropdown.Toggle>
            <span>{title}</span>
          </Dropdown.Toggle>
          <Dropdown.Menu>{children && children.map(menuItem => React.cloneElement(menuItem))}</Dropdown.Menu>
        </Dropdown>
      );
    }

    return (
      <Dropdown id={id || helpers.generateId()} open={dropdownIsOpen} onToggle={toggleDropDown} {...filteredProps}>
        <Dropdown.Toggle>
          <span>{title}</span>
        </Dropdown.Toggle>
        <Dropdown.Menu>
          {children &&
            children.map(menuItem => React.cloneElement(menuItem, { onClick: passOnClick(menuItem.props.onClick) }))}
        </Dropdown.Menu>
      </Dropdown>
    );
  }
}

DropdownSelect.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.string.isRequired,
  id: PropTypes.string,
  multiselect: PropTypes.bool
};

export default DropdownSelect;
