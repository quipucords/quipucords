import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Button,
  EmptyState,
  Icon,
  ListView,
  Modal
} from 'patternfly-react';

import { getSources } from '../../redux/actions/sourcesActions';
import {
  sourcesTypes,
  toastNotificationTypes,
  confirmationModalTypes,
  viewTypes
} from '../../redux/constants';
import Store from '../../redux/store';
import helpers from '../../common/helpers';

import ViewToolbar from '../viewToolbar/viewToolbar';
import ViewPaginationRow from '../viewPaginationRow/viewPaginationRow';

import SourcesEmptyState from './sourcesEmptyState';
import { SourceListItem } from './sourceListItem';
import { CreateScanDialog } from './createScanDialog';
import { AddSourceWizard } from './addSourceWizard';
import { SourceFilterFields, SourceSortFields } from './sourceConstants';

class Sources extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
      'importSources',
      'scanSource',
      'scanSources',
      'itemSelectChange',
      'editSource',
      'deleteSource',
      'hideScanDialog',
      'createScan',
      'refresh',
      'showAddSourceWizard',
      'quitAddSourceWizard'
    ]);

    this.state = {
      selectedItems: [],
      scanDialogShown: false,
      multiSourceScan: false,
      currentScanSource: null,
      addSourceWizardShown: false
    };
  }

  componentDidMount() {
    this.props.getSources(helpers.viewQueryObject(this.props.viewOptions));
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.sources && nextProps.sources !== this.props.sources) {
      // Reset selection state though we may want to keep selections over refreshes...
      nextProps.sources.forEach(source => {
        source.selected = false;
      });

      // TODO: Remove once we get real failed host data
      nextProps.sources.forEach(source => {
        let failedCount = Math.floor(Math.random() * 10);
        source.failed_hosts = [];
        for (let i = 0; i < failedCount; i++) {
          source.failed_hosts.push('failedHost' + (i + 1));
        }
      });

      this.setState({ selectedItems: [] });
    }

    // Check for changes resulting in a fetch
    if (
      helpers.viewPropsChanged(nextProps.viewOptions, this.props.viewOptions)
    ) {
      this.props.getSources(helpers.viewQueryObject(nextProps.viewOptions));
    }
  }

  showAddSourceWizard() {
    this.setState({ addSourceWizardShown: true });
  }

  quitAddSourceWizard() {
    let onConfirm = () => {
      Store.dispatch({
        type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
      });

      this.setState({ addSourceWizardShown: false });
    };

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Cancel Add Source',
      heading: 'Are you sure you want to exit this wizard?',
      body: 'Exiting this wizard will cancel adding the source.',
      cancelButtonText: 'No',
      confirmButtonText: 'Yes',
      onConfirm: onConfirm
    });
  }

  importSources() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Importing sources is not yet implemented'
    });
  }

  scanSource(source) {
    this.setState({
      scanDialogShown: true,
      multiSourceScan: false,
      currentScanSource: source
    });
  }

  scanSources() {
    this.setState({ scanDialogShown: true, multiSourceScan: true });
  }

  hideScanDialog() {
    this.setState({ scanDialogShown: false });
  }

  itemSelectChange(item) {
    const { filteredItems } = this.state;

    item.selected = !item.selected;
    let selectedItems = filteredItems.filter(item => {
      return item.selected === true;
    });

    this.setState({ selectedItems: selectedItems });

    Store.dispatch({
      type: sourcesTypes.SOURCES_SELECTED,
      selectedSources: selectedItems
    });
  }

  editSource(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Editing sources is not yet implemented'
    });
  }

  doDeleteSource(item) {
    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    });

    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Deleting sources is not yet implemented'
    });
  }

  deleteSource(item) {
    let heading = (
      <span>
        Are you sure you want to delete the source <strong>{item.name}</strong>?
      </span>
    );

    let onConfirm = () => this.doDeleteSource(item);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Source',
      heading: heading,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  createScan(scanName, sources) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: scanName,
      message: 'Scanning sources is not yet implemented'
    });
    this.hideScanDialog();
  }

  refresh() {
    this.props.getSources();
  }

  renderActions() {
    const { selectedItems } = this.state;

    return (
      <div className="form-group">
        <Button bsStyle="primary" onClick={this.showAddSourceWizard}>
          Add
        </Button>
        <Button
          disabled={!selectedItems || selectedItems.length === 0}
          onClick={this.scanSources}
        >
          Scan
        </Button>
        <Button onClick={this.refresh} bsStyle="success">
          <Icon type="fa" name="refresh" />
        </Button>
      </div>
    );
  }

  renderList(items) {
    return (
      <ListView className="quipicords-list-view">
        {items.map((item, index) => (
          <SourceListItem
            item={item}
            key={index}
            onItemSelectChange={this.itemSelectChange}
            onEdit={this.editSource}
            onDelete={this.deleteSource}
            onScan={this.scanSource}
          />
        ))}
      </ListView>
    );
  }

  render() {
    const { pending, error, errorMessage, sources, viewOptions } = this.props;
    const {
      selectedItems,
      scanDialogShown,
      multiSourceScan,
      currentScanSource,
      addSourceWizardShown
    } = this.state;

    if (pending) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading sources...</div>
          </Modal.Body>
        </Modal>
      );
    }

    if (error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving sources: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (sources && sources.length) {
      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={viewTypes.SOURCES_VIEW}
              filterFields={SourceFilterFields}
              sortFields={SourceSortFields}
              actions={this.renderActions()}
              itemsType="Source"
              itemsTypePlural="Sources"
              {...viewOptions}
            />
            <div className="quipucords-list-container">
              {this.renderList(sources)}
            </div>
            <ViewPaginationRow
              viewType={viewTypes.SOURCES_VIEW}
              {...viewOptions}
            />
          </div>
          <AddSourceWizard
            show={addSourceWizardShown}
            onCancel={this.quitAddSourceWizard}
          />
          <CreateScanDialog
            show={scanDialogShown}
            sources={multiSourceScan ? selectedItems : [currentScanSource]}
            onCancel={this.hideScanDialog}
            onScan={this.createScan}
          />
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        <SourcesEmptyState
          onAddSource={this.showAddSourceWizard}
          onImportSources={this.importSources}
        />
        <AddSourceWizard
          show={addSourceWizardShown}
          onCancel={this.quitAddSourceWizard}
        />
      </React.Fragment>
    );
  }
}

Sources.propTypes = {
  getSources: PropTypes.func,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  sources: PropTypes.array,
  viewOptions: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getSources: () => dispatch(getSources())
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.sources.view, state.sources.persist, {
    viewOptions: state.viewOptions[viewTypes.SOURCES_VIEW]
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(Sources);
