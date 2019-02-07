import React from 'react';
import PropTypes from 'prop-types';
import { Dropdown, Grid, Icon, MenuItem } from 'patternfly-react';
import _isPlainObject from 'lodash/isPlainObject';
import _cloneDeep from 'lodash/cloneDeep';
import helpers from '../../common/helpers';

class DropdownSelect extends React.Component {
  static filterTitle(options, multiselect) {
    const title = [];

    for (let i = 0; i < options.length; i++) {
      if (options[i].active === true && options[i].title) {
        title.push(options[i].title);
      }

      if (!multiselect && title.length > 0) {
        break;
      }
    }

    return title.length ? title.join(',') : null;
  }

  state = {
    isOpen: false,
    options: null,
    selectedTitle: []
  };

  componentDidMount() {
    const { options } = this.state;

    if (options === null) {
      this.formatFilterOptions();
    }
  }

  onSelect = value => {
    const { options } = this.state;
    const { multiselect, onSelect } = this.props;
    const updatedOptions = _cloneDeep(options);

    const optionsIndex = updatedOptions.findIndex(option => option.value === value);

    updatedOptions[optionsIndex].active = !multiselect ? true : !updatedOptions[optionsIndex].active;

    if (!multiselect) {
      updatedOptions.forEach((option, index) => {
        if (optionsIndex !== index) {
          updatedOptions[index].active = false;
        }
      });
    }

    const updatedSelectedTitle = DropdownSelect.filterTitle(updatedOptions, multiselect);

    this.setState(
      {
        selectedTitle: updatedSelectedTitle,
        options: updatedOptions
      },
      () => {
        onSelect(updatedOptions[optionsIndex], optionsIndex, updatedOptions);
      }
    );
  };

  onToggleDropDown = (a, b, c) => {
    const { isOpen } = this.state;

    this.setState({
      isOpen: (c && c.source === 'select') || !isOpen
    });
  };

  formatFilterOptions() {
    const { options, multiselect, selectValue } = this.props;
    const updatedOptions = _isPlainObject(options)
      ? Object.keys(options).map(value => ({ title: options[value], value }))
      : _cloneDeep(options);

    const updatedTitle = [];
    const activateValues = selectValue && typeof selectValue === 'string' ? [selectValue] : selectValue;

    updatedOptions.forEach((option, index) => {
      let convertedOption = option;

      if (typeof convertedOption === 'string') {
        convertedOption = {
          title: option,
          value: option
        };

        updatedOptions[index] = convertedOption;
      }

      if (activateValues) {
        updatedOptions[index].active = activateValues.includes(convertedOption.value);
      }

      if (convertedOption.active === true) {
        if (!multiselect && updatedTitle.length) {
          updatedOptions[index].active = false;
        }

        if (multiselect || (!multiselect && !updatedTitle.length)) {
          updatedTitle.push(convertedOption.title);
        }
      }
    });

    this.setState({
      selectedTitle: updatedTitle.length ? updatedTitle.join(',') : null,
      options: updatedOptions
    });
  }

  render() {
    const { isOpen, options, selectedTitle } = this.state;
    const { className, id, multiselect, pullRight, title } = this.props;
    const multiselectProps = {};

    if (multiselect) {
      multiselectProps.onToggle = this.onToggleDropDown;
      multiselectProps.open = isOpen;
    }

    return (
      <Dropdown
        id={id}
        disabled={!options || !options.length}
        className={`quipucords-dropdownselect ${className}`}
        onSelect={this.onSelect}
        pullRight={pullRight}
        {...multiselectProps}
      >
        <Dropdown.Toggle>
          <span>{selectedTitle || title}</span>
        </Dropdown.Toggle>
        <Dropdown.Menu>
          {options &&
            options.map(option => (
              <MenuItem key={option.value} eventKey={option.value} active={!multiselect && option.active}>
                {!multiselect && option.title}
                {multiselect && (
                  <Grid.Row className="quipucords-dropdownselect-menuitem">
                    <Grid.Col xs={10} className="quipucords-dropdownselect-menuitemname">
                      {option.title}
                    </Grid.Col>
                    <Grid.Col xs={2} className="quipucords-dropdownselect-menuitemcheck">
                      {option.active && <Icon type="fa" name="check" />}
                    </Grid.Col>
                  </Grid.Row>
                )}
              </MenuItem>
            ))}
        </Dropdown.Menu>
      </Dropdown>
    );
  }
}

DropdownSelect.propTypes = {
  className: PropTypes.string,
  id: PropTypes.string,
  multiselect: PropTypes.bool,
  onSelect: PropTypes.func,
  options: PropTypes.oneOfType([PropTypes.array, PropTypes.object]),
  pullRight: PropTypes.bool,
  selectValue: PropTypes.oneOfType([PropTypes.string, PropTypes.array]),
  title: PropTypes.string
};

DropdownSelect.defaultProps = {
  className: '',
  id: helpers.generateId(),
  multiselect: false,
  onSelect: helpers.noop,
  options: [],
  pullRight: false,
  selectValue: null,
  title: 'Select option'
};

export { DropdownSelect as default, DropdownSelect };
